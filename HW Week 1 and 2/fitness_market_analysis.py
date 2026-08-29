#!/usr/bin/env python3
"""Florida fitness-market analysis for the Week 1 and 2 assignment.

Observed data:
  * 2020 Census PL 94-171 county population (P1_001N)
  * 2021 ACS 5-year median household income (B19013_001E)
  * 2020 Census Gazetteer county land area and internal-point coordinates
  * Google Places branded gym locations, ratings, and rating counts

Estimated data:
  * County-level average monthly membership prices

The price field is permitted by the assignment when comparable county-level price
data cannot be obtained. It is deterministic (seed 6642), explicitly labeled in
the source register, and must not be represented as an observed transaction series.
"""

from __future__ import annotations

import io
import json
import math
import time
import warnings
import zipfile
from datetime import datetime, timezone
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import requests
import seaborn as sns
import statsmodels.api as sm
from scipy.stats import shapiro
from statsmodels.stats.diagnostic import het_breuschpagan
from statsmodels.stats.outliers_influence import variance_inflation_factor


ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
OUTPUT_DIR = ROOT / "outputs"
FIGURE_DIR = OUTPUT_DIR / "figures"
KEY_PATH = ROOT / "census_api_key.txt"
GOOGLE_KEY_PATH = ROOT / "google_places_api_key.txt"
RANDOM_SEED = 6642

POPULATION_URL = "https://api.census.gov/data/2020/dec/pl"
INCOME_URL = "https://api.census.gov/data/2021/acs/acs5"
GAZETTEER_URL = (
    "https://www2.census.gov/geo/docs/maps-data/data/gazetteer/"
    "2020_Gazetteer/2020_Gaz_counties_national.zip"
)
PLACES_TEXT_SEARCH_URL = "https://places.googleapis.com/v1/places:searchText"

SOURCE_ROWS = [
    {
        "Dataset": "County population",
        "Status": "Observed",
        "Vintage": "2020 Census PL 94-171",
        "Variable": "P1_001N",
        "URL": POPULATION_URL,
        "Notes": "Total population for all Florida counties.",
    },
    {
        "Dataset": "Median household income",
        "Status": "Observed estimate",
        "Vintage": "2021 ACS 5-year",
        "Variable": "B19013_001E",
        "URL": INCOME_URL,
        "Notes": "Income is expressed in 2021 inflation-adjusted dollars.",
    },
    {
        "Dataset": "County land area and internal point",
        "Status": "Observed",
        "Vintage": "2020 Census Gazetteer",
        "Variable": "ALAND_SQMI, INTPTLAT, INTPTLONG",
        "URL": GAZETTEER_URL,
        "Notes": "Land area is used to derive population density.",
    },
    {
        "Dataset": "Gym locations, ratings, and reviews",
        "Status": "Observed API results",
        "Vintage": "Google Places API (New); retrieval date recorded in run metadata",
        "Variable": "Place ID, name, county, coordinates, rating, and rating count",
        "URL": "https://developers.google.com/maps/documentation/places/web-service/text-search",
        "Notes": (
            "County-by-county branded Text Search with exact-county filtering and Place ID "
            "deduplication. Results reflect Google's response at retrieval time and may not "
            "be exhaustive."
        ),
    },
    {
        "Dataset": "Membership price",
        "Status": "SIMULATED",
        "Vintage": "Assignment scenario",
        "Variable": "MembershipPrice",
        "URL": "https://www.lafitness.com/Pages/MembershipSignUpRate.aspx",
        "Notes": (
            "County estimates are generated from a transparent model anchored to public "
            "chain price points; they are not surveyed county averages."
        ),
    },
]

MODEL_VARIABLES = [
    "CountyPopulation",
    "LAFitnessLocations",
    "CompetitorLocations",
    "MedianHouseholdIncome",
    "PopulationDensity",
    "AvgGymRating",
]

NAVY = "#12355B"
TEAL = "#2A9D8F"
GOLD = "#D99A2B"
RED = "#B04A5A"
LIGHT = "#EEF3F7"


def ensure_directories() -> None:
    for path in (DATA_DIR, OUTPUT_DIR, FIGURE_DIR):
        path.mkdir(parents=True, exist_ok=True)


def load_census_key() -> str:
    if not KEY_PATH.exists():
        raise FileNotFoundError(
            f"Missing {KEY_PATH.name}. Place a Census API key beside this script."
        )
    key = KEY_PATH.read_text(encoding="utf-8").strip()
    if len(key) < 20 or any(ch.isspace() for ch in key):
        raise ValueError("The Census API key file does not contain a valid-looking key.")
    return key


def load_google_places_key() -> str:
    if not GOOGLE_KEY_PATH.exists():
        raise FileNotFoundError(
            f"Missing {GOOGLE_KEY_PATH.name}. Place a Google Places API key beside this script."
        )
    key = GOOGLE_KEY_PATH.read_text(encoding="utf-8").strip()
    if len(key) < 20 or any(ch.isspace() for ch in key):
        raise ValueError("The Google Places API key file does not contain a valid-looking key.")
    return key


def census_county_request(url: str, variable: str, api_key: str) -> pd.DataFrame:
    params = {
        "get": f"NAME,{variable}",
        "for": "county:*",
        "in": "state:12",
        "key": api_key,
    }
    response = requests.get(url, params=params, timeout=90)
    if response.status_code != 200:
        raise RuntimeError(f"Census API request failed with HTTP {response.status_code}.")
    try:
        payload = response.json()
    except requests.JSONDecodeError as exc:
        raise RuntimeError("Census API returned a non-JSON response.") from exc
    if len(payload) != 68:
        raise RuntimeError(f"Expected header plus 67 counties; received {len(payload)} rows.")
    frame = pd.DataFrame(payload[1:], columns=payload[0])
    frame["CountyFIPS"] = frame["state"] + frame["county"]
    frame["CountyName"] = frame["NAME"].str.replace(", Florida", "", regex=False)
    frame[variable] = pd.to_numeric(frame[variable], errors="raise")
    return frame[["CountyFIPS", "CountyName", variable]]


def download_gazetteer() -> pd.DataFrame:
    response = requests.get(GAZETTEER_URL, timeout=90)
    if response.status_code != 200:
        raise RuntimeError(f"Gazetteer download failed with HTTP {response.status_code}.")
    with zipfile.ZipFile(io.BytesIO(response.content)) as archive:
        members = [name for name in archive.namelist() if name.endswith(".txt")]
        if len(members) != 1:
            raise RuntimeError("Unexpected Gazetteer ZIP structure.")
        with archive.open(members[0]) as handle:
            gaz = pd.read_csv(handle, sep="\t", dtype={"GEOID": str})
    gaz.columns = [column.strip() for column in gaz.columns]
    gaz = gaz.loc[gaz["USPS"].eq("FL")].copy()
    gaz["CountyFIPS"] = gaz["GEOID"].str.zfill(5)
    gaz["CountyName"] = gaz["NAME"].str.strip()
    gaz["LandAreaSqMiles"] = pd.to_numeric(gaz["ALAND_SQMI"], errors="raise")
    gaz["Latitude"] = pd.to_numeric(gaz["INTPTLAT"], errors="raise")
    gaz["Longitude"] = pd.to_numeric(gaz["INTPTLONG"], errors="raise")
    return gaz[
        ["CountyFIPS", "CountyName", "LandAreaSqMiles", "Latitude", "Longitude"]
    ]


def collect_demographics() -> tuple[pd.DataFrame, pd.DataFrame]:
    api_key = load_census_key()
    population = census_county_request(POPULATION_URL, "P1_001N", api_key).rename(
        columns={"P1_001N": "CountyPopulation"}
    )
    income = census_county_request(INCOME_URL, "B19013_001E", api_key).rename(
        columns={"B19013_001E": "MedianHouseholdIncome"}
    )
    gazetteer = download_gazetteer()

    merged = population.merge(
        income[["CountyFIPS", "MedianHouseholdIncome"]],
        on="CountyFIPS",
        validate="one_to_one",
    ).merge(
        gazetteer.drop(columns="CountyName"),
        on="CountyFIPS",
        validate="one_to_one",
    )
    merged["PopulationDensity"] = (
        merged["CountyPopulation"] / merged["LandAreaSqMiles"]
    )
    merged = merged.sort_values("CountyName").reset_index(drop=True)

    if len(merged) != 67 or merged["CountyFIPS"].nunique() != 67:
        raise RuntimeError("The demographic merge did not produce 67 unique Florida counties.")
    if merged[MODEL_VARIABLES[:1] + ["MedianHouseholdIncome", "PopulationDensity"]].isna().any().any():
        raise RuntimeError("Required demographic fields contain missing values.")

    demographics = merged[
        [
            "CountyName",
            "CountyPopulation",
            "MedianHouseholdIncome",
            "LandAreaSqMiles",
            "PopulationDensity",
        ]
    ].copy()
    demographics["LandAreaSqMiles"] = demographics["LandAreaSqMiles"].round(3)
    demographics["PopulationDensity"] = demographics["PopulationDensity"].round(3)
    demographics.to_csv(DATA_DIR / "demographic_data.csv", index=False)
    return demographics, merged


def minmax(series: pd.Series) -> pd.Series:
    span = float(series.max() - series.min())
    if math.isclose(span, 0.0):
        return pd.Series(np.zeros(len(series)), index=series.index)
    return (series - series.min()) / span


def extract_county_name(address_components: list[dict[str, object]]) -> str | None:
    for component in address_components:
        types = component.get("types", [])
        if "administrative_area_level_2" in types:
            long_text = str(component.get("longText", "")).strip()
            return long_text or None
    return None


def brand_name_matches(display_name: str, aliases: tuple[str, ...]) -> bool:
    normalized = display_name.casefold().replace("’", "'")
    return any(alias in normalized for alias in aliases)


def places_search_pages(
    session: requests.Session,
    api_key: str,
    query: str,
) -> list[dict[str, object]]:
    field_mask = ",".join(
        [
            "places.id",
            "places.displayName",
            "places.formattedAddress",
            "places.addressComponents",
            "places.location",
            "places.rating",
            "places.userRatingCount",
            "nextPageToken",
        ]
    )
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": api_key,
        "X-Goog-FieldMask": field_mask,
    }
    base_body: dict[str, object] = {
        "textQuery": query,
        "pageSize": 20,
        "languageCode": "en",
        "regionCode": "US",
    }
    page_token: str | None = None
    places: list[dict[str, object]] = []
    for _page_number in range(3):
        body = dict(base_body)
        if page_token:
            body["pageToken"] = page_token
        for attempt in range(4):
            response = session.post(
                PLACES_TEXT_SEARCH_URL,
                headers=headers,
                json=body,
                timeout=90,
            )
            if response.status_code == 200:
                break
            if response.status_code in {429, 500, 502, 503, 504} and attempt < 3:
                time.sleep(2**attempt)
                continue
            try:
                error_message = str(response.json().get("error", {}).get("message", ""))
            except requests.JSONDecodeError:
                error_message = ""
            detail = f" {error_message}" if error_message else ""
            raise RuntimeError(
                f"Google Places request failed with HTTP {response.status_code}.{detail}"
            )
        payload = response.json()
        places.extend(payload.get("places", []))
        page_token = payload.get("nextPageToken")
        if not page_token:
            break
    return places


def collect_google_places(demographic_internal: pd.DataFrame) -> pd.DataFrame:
    api_key = load_google_places_key()
    brand_aliases: dict[str, tuple[str, ...]] = {
        "LA Fitness": ("la fitness",),
        "Planet Fitness": ("planet fitness",),
        "24 Hour Fitness": ("24 hour fitness",),
        "Gold's Gym": ("gold's gym", "golds gym"),
        "Orangetheory Fitness": ("orangetheory", "orange theory"),
    }
    rows_by_place_id: dict[str, dict[str, object]] = {}
    query_audit: list[dict[str, object]] = []
    session = requests.Session()

    county_names = demographic_internal["CountyName"].tolist()
    for county_index, county_name in enumerate(county_names, start=1):
        for canonical_chain, aliases in brand_aliases.items():
            query = f"{canonical_chain} in {county_name}, Florida"
            returned = places_search_pages(session, api_key, query)
            accepted = 0
            for place in returned:
                place_id = str(place.get("id", "")).strip()
                display_name = str(place.get("displayName", {}).get("text", "")).strip()
                place_county = extract_county_name(place.get("addressComponents", []))
                location = place.get("location", {})
                if not place_id or not display_name or place_county != county_name:
                    continue
                if not brand_name_matches(display_name, aliases):
                    continue
                latitude = location.get("latitude")
                longitude = location.get("longitude")
                if latitude is None or longitude is None:
                    continue
                rating = place.get("rating")
                review_count = place.get("userRatingCount")
                rows_by_place_id[place_id] = {
                    "LocationID": place_id,
                    "GymChain": canonical_chain,
                    "CountyName": county_name,
                    "Latitude": round(float(latitude), 7),
                    "Longitude": round(float(longitude), 7),
                    "Rating": float(rating) if rating is not None else np.nan,
                    "ReviewCount": int(review_count) if review_count is not None else 0,
                }
                accepted += 1
            query_audit.append(
                {
                    "CountyName": county_name,
                    "GymChain": canonical_chain,
                    "ReturnedCandidates": len(returned),
                    "AcceptedExactCountyBrandMatches": accepted,
                }
            )
        if county_index == 1 or county_index % 10 == 0 or county_index == len(county_names):
            print(
                f"Google Places progress: {county_index}/{len(county_names)} counties",
                flush=True,
            )

    locations = pd.DataFrame(rows_by_place_id.values())
    if locations.empty:
        raise RuntimeError("Google Places collection produced no accepted gym records.")
    locations = locations.sort_values(["CountyName", "GymChain", "LocationID"])
    locations["Rating"] = locations["Rating"].round(1)
    locations.to_csv(DATA_DIR / "gym_locations.csv", index=False)
    pd.DataFrame(query_audit).to_csv(OUTPUT_DIR / "places_query_audit.csv", index=False)
    return locations


def build_main_dataset(
    demographics: pd.DataFrame, locations: pd.DataFrame
) -> tuple[pd.DataFrame, pd.DataFrame]:
    la_counts = (
        locations.loc[locations["GymChain"].eq("LA Fitness")]
        .groupby("CountyName")
        .size()
        .rename("LAFitnessLocations")
    )
    competitor_counts = (
        locations.loc[~locations["GymChain"].eq("LA Fitness")]
        .groupby("CountyName")
        .size()
        .rename("CompetitorLocations")
    )
    avg_rating = locations.groupby("CountyName")["Rating"].mean().rename("AvgGymRating")

    market = demographics.merge(la_counts, on="CountyName", how="left").merge(
        competitor_counts, on="CountyName", how="left"
    ).merge(avg_rating, on="CountyName", how="left")
    market[["LAFitnessLocations", "CompetitorLocations"]] = market[
        ["LAFitnessLocations", "CompetitorLocations"]
    ].fillna(0).astype(int)
    missing_rating = market["AvgGymRating"].isna()
    rating_imputation_value = float(locations["Rating"].median())
    market["AvgGymRating"] = market["AvgGymRating"].fillna(rating_imputation_value)
    market["AvgGymRating"] = market["AvgGymRating"].round(3)

    rng = np.random.default_rng(RANDOM_SEED + 1)
    noise = rng.normal(0, 2.0, len(market))
    market["MembershipPrice"] = (
        8.0
        + 0.0000015 * market["CountyPopulation"]
        + 0.45 * market["LAFitnessLocations"]
        - 0.12 * market["CompetitorLocations"]
        + 0.00012 * market["MedianHouseholdIncome"]
        + 0.0010 * market["PopulationDensity"]
        + 5.0 * market["AvgGymRating"]
        + noise
    ).clip(24, 55).round(2)

    membership = market[["CountyName", "MembershipPrice"]].copy()
    membership.to_csv(DATA_DIR / "membership_prices.csv", index=False)

    main = market[
        [
            "CountyName",
            "MembershipPrice",
            "CountyPopulation",
            "LAFitnessLocations",
            "CompetitorLocations",
            "MedianHouseholdIncome",
            "PopulationDensity",
            "AvgGymRating",
        ]
    ].copy()
    main["PopulationDensity"] = main["PopulationDensity"].round(3)
    main.to_csv(DATA_DIR / "MainDataset.csv", index=False)

    quality = pd.DataFrame(
        [
            {
                "Check": "Florida county rows",
                "Result": len(main),
                "Expected": 67,
                "Status": "PASS" if len(main) == 67 else "FAIL",
            },
            {
                "Check": "Unique county names",
                "Result": main["CountyName"].nunique(),
                "Expected": 67,
                "Status": "PASS" if main["CountyName"].nunique() == 67 else "FAIL",
            },
            {
                "Check": "Missing values in MainDataset",
                "Result": int(main.isna().sum().sum()),
                "Expected": 0,
                "Status": "PASS" if not main.isna().any().any() else "FAIL",
            },
            {
                "Check": "Counties with imputed average rating",
                "Result": int(missing_rating.sum()),
                "Expected": "Documented",
                "Status": "PASS",
            },
            {
                "Check": "Rating imputation value",
                "Result": round(rating_imputation_value, 2),
                "Expected": "Statewide median of observed Google Places ratings",
                "Status": "PASS",
            },
        ]
    )
    quality.to_csv(OUTPUT_DIR / "data_quality_checks.csv", index=False)
    return main, quality


def configure_plot_style() -> None:
    sns.set_theme(style="whitegrid", context="notebook")
    plt.rcParams.update(
        {
            "figure.facecolor": "white",
            "axes.facecolor": "white",
            "axes.edgecolor": "#AEB8C2",
            "axes.labelcolor": "#263746",
            "axes.titlecolor": NAVY,
            "axes.titleweight": "bold",
            "font.family": "DejaVu Sans",
            "savefig.facecolor": "white",
        }
    )


def save_current_figure(filename: str) -> None:
    plt.tight_layout()
    plt.savefig(FIGURE_DIR / filename, dpi=220, bbox_inches="tight")
    plt.close()


def create_eda_outputs(main: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    numeric = main.drop(columns="CountyName")
    summary = numeric.describe().T[
        ["count", "mean", "50%", "std", "min", "max"]
    ].rename(columns={"count": "Count", "mean": "Mean", "50%": "Median", "std": "StdDev", "min": "Min", "max": "Max"})
    summary.to_csv(OUTPUT_DIR / "summary_statistics.csv")
    correlation = numeric.corr()
    correlation.to_csv(OUTPUT_DIR / "correlation_matrix.csv")

    configure_plot_style()

    plt.figure(figsize=(8.0, 5.0))
    sns.regplot(
        data=main,
        x="CountyPopulation",
        y="MembershipPrice",
        scatter_kws={"color": NAVY, "alpha": 0.72, "s": 42},
        line_kws={"color": GOLD, "linewidth": 2.2},
    )
    plt.xlabel("County population")
    plt.ylabel("Estimated monthly membership price (USD)")
    plt.title("Larger county markets generally support higher estimated prices")
    plt.ticklabel_format(style="plain", axis="x")
    save_current_figure("01_population_vs_price.png")

    plt.figure(figsize=(8.0, 5.0))
    sns.regplot(
        data=main,
        x="MedianHouseholdIncome",
        y="MembershipPrice",
        scatter_kws={"color": TEAL, "alpha": 0.76, "s": 42},
        line_kws={"color": GOLD, "linewidth": 2.2},
    )
    plt.xlabel("Median household income (2021 USD)")
    plt.ylabel("Estimated monthly membership price (USD)")
    plt.title("Purchasing power is positively associated with estimated price")
    save_current_figure("02_income_vs_price.png")

    plt.figure(figsize=(8.0, 5.0))
    sns.regplot(
        data=main,
        x="LAFitnessLocations",
        y="MembershipPrice",
        x_jitter=0.08,
        scatter_kws={"color": NAVY, "alpha": 0.72, "s": 42},
        line_kws={"color": GOLD, "linewidth": 2.2},
    )
    plt.xlabel("Observed LA Fitness location count")
    plt.ylabel("Estimated monthly membership price (USD)")
    plt.title("Existing LA Fitness presence and estimated market price")
    save_current_figure("03_la_locations_vs_price.png")

    plt.figure(figsize=(8.0, 5.0))
    sns.histplot(main["MembershipPrice"], bins=12, color=TEAL, edgecolor="white")
    plt.axvline(main["MembershipPrice"].mean(), color=GOLD, linewidth=2.2, label="Mean")
    plt.xlabel("Estimated monthly membership price (USD)")
    plt.ylabel("Number of counties")
    plt.title("Distribution of simulated county membership prices")
    plt.legend(frameon=False)
    save_current_figure("04_price_histogram.png")

    plt.figure(figsize=(9.2, 7.0))
    mask = np.triu(np.ones_like(correlation, dtype=bool), k=1)
    sns.heatmap(
        correlation,
        mask=mask,
        cmap=sns.diverging_palette(220, 35, as_cmap=True),
        center=0,
        vmin=-1,
        vmax=1,
        annot=True,
        fmt=".2f",
        square=True,
        linewidths=0.6,
        cbar_kws={"shrink": 0.78, "label": "Pearson correlation"},
    )
    plt.title("Correlation matrix highlights related market-size variables")
    plt.xticks(rotation=42, ha="right")
    plt.yticks(rotation=0)
    save_current_figure("05_correlation_heatmap.png")
    return summary, correlation


def coefficient_table(model: sm.regression.linear_model.RegressionResultsWrapper) -> pd.DataFrame:
    conf = model.conf_int(alpha=0.05)
    return pd.DataFrame(
        {
            "Variable": model.params.index,
            "Coefficient": model.params.values,
            "StdError": model.bse.values,
            "tStatistic": model.tvalues.values,
            "pValue": model.pvalues.values,
            "CI95Lower": conf[0].values,
            "CI95Upper": conf[1].values,
        }
    )


def fit_models(main: pd.DataFrame) -> dict[str, object]:
    y = main["MembershipPrice"]
    x_full = sm.add_constant(main[MODEL_VARIABLES], has_constant="add")
    full_model = sm.OLS(y, x_full).fit()

    vif_rows = []
    for index, variable in enumerate(MODEL_VARIABLES, start=1):
        vif_rows.append(
            {
                "Variable": variable,
                "VIF": variance_inflation_factor(x_full.values, index),
                "FlagAbove5": variance_inflation_factor(x_full.values, index) > 5,
            }
        )
    vif = pd.DataFrame(vif_rows)
    vif.to_csv(OUTPUT_DIR / "vif.csv", index=False)

    selected = MODEL_VARIABLES.copy()
    elimination_log: list[dict[str, object]] = []
    while len(selected) > 1:
        candidate = sm.OLS(
            y, sm.add_constant(main[selected], has_constant="add")
        ).fit()
        non_intercept_p = candidate.pvalues.drop("const")
        max_variable = str(non_intercept_p.idxmax())
        max_p = float(non_intercept_p.max())
        if max_p <= 0.05:
            break
        elimination_log.append(
            {"RemovedVariable": max_variable, "pValueAtRemoval": max_p}
        )
        selected.remove(max_variable)
    refined_model = sm.OLS(
        y, sm.add_constant(main[selected], has_constant="add")
    ).fit()

    full_coefficients = coefficient_table(full_model)
    refined_coefficients = coefficient_table(refined_model)
    full_coefficients.to_csv(OUTPUT_DIR / "regression_full_coefficients.csv", index=False)
    refined_coefficients.to_csv(
        OUTPUT_DIR / "regression_refined_coefficients.csv", index=False
    )
    pd.DataFrame(elimination_log).to_csv(
        OUTPUT_DIR / "model_elimination_log.csv", index=False
    )
    (OUTPUT_DIR / "full_model_summary.txt").write_text(
        full_model.summary().as_text(), encoding="utf-8"
    )
    (OUTPUT_DIR / "refined_model_summary.txt").write_text(
        refined_model.summary().as_text(), encoding="utf-8"
    )

    comparison = pd.DataFrame(
        [
            {
                "Model": "Full",
                "Predictors": ", ".join(MODEL_VARIABLES),
                "N": int(full_model.nobs),
                "R2": full_model.rsquared,
                "AdjustedR2": full_model.rsquared_adj,
                "AIC": full_model.aic,
                "BIC": full_model.bic,
                "RMSE": float(np.sqrt(np.mean(full_model.resid**2))),
            },
            {
                "Model": "Refined",
                "Predictors": ", ".join(selected),
                "N": int(refined_model.nobs),
                "R2": refined_model.rsquared,
                "AdjustedR2": refined_model.rsquared_adj,
                "AIC": refined_model.aic,
                "BIC": refined_model.bic,
                "RMSE": float(np.sqrt(np.mean(refined_model.resid**2))),
            },
        ]
    )
    comparison.to_csv(OUTPUT_DIR / "model_comparison.csv", index=False)

    shapiro_stat, shapiro_p = shapiro(refined_model.resid)
    bp_stat, bp_p, bp_f_stat, bp_f_p = het_breuschpagan(
        refined_model.resid, refined_model.model.exog
    )
    diagnostics = pd.DataFrame(
        [
            {
                "Test": "Shapiro-Wilk residual normality",
                "Statistic": shapiro_stat,
                "pValue": shapiro_p,
                "Interpretation": (
                    "No evidence against normality"
                    if shapiro_p >= 0.05
                    else "Residual normality concern"
                ),
            },
            {
                "Test": "Breusch-Pagan homoscedasticity",
                "Statistic": bp_stat,
                "pValue": bp_p,
                "Interpretation": (
                    "No evidence of heteroscedasticity"
                    if bp_p >= 0.05
                    else "Heteroscedasticity concern"
                ),
            },
            {
                "Test": "Breusch-Pagan F version",
                "Statistic": bp_f_stat,
                "pValue": bp_f_p,
                "Interpretation": (
                    "No evidence of heteroscedasticity"
                    if bp_f_p >= 0.05
                    else "Heteroscedasticity concern"
                ),
            },
        ]
    )
    diagnostics.to_csv(OUTPUT_DIR / "diagnostic_tests.csv", index=False)

    influence = refined_model.get_influence()
    influence_frame = pd.DataFrame(
        {
            "CountyName": main["CountyName"],
            "StudentizedResidual": influence.resid_studentized_external,
            "CooksDistance": influence.cooks_distance[0],
            "Leverage": influence.hat_matrix_diag,
        }
    )
    cooks_threshold = 4 / len(main)
    influence_frame["Flag"] = np.where(
        (influence_frame["CooksDistance"] > cooks_threshold)
        | (influence_frame["StudentizedResidual"].abs() > 2),
        "Review",
        "No flag",
    )
    flagged = influence_frame.loc[influence_frame["Flag"].eq("Review")].sort_values(
        "CooksDistance", ascending=False
    )
    influence_frame.to_csv(OUTPUT_DIR / "influence_diagnostics.csv", index=False)
    flagged.to_csv(OUTPUT_DIR / "outliers.csv", index=False)

    predicted = refined_model.fittedvalues
    residuals = refined_model.resid
    configure_plot_style()

    plt.figure(figsize=(7.2, 5.2))
    plt.scatter(y, predicted, color=NAVY, alpha=0.78, s=44)
    limits = [min(y.min(), predicted.min()), max(y.max(), predicted.max())]
    plt.plot(limits, limits, color=GOLD, linewidth=2.1, linestyle="--")
    plt.xlabel("Actual estimated price (USD)")
    plt.ylabel("Model-predicted price (USD)")
    plt.title("Refined model predictions track simulated county prices")
    save_current_figure("06_actual_vs_predicted.png")

    fig = sm.qqplot(residuals, line="45", fit=True, markerfacecolor=TEAL, markeredgecolor="white")
    fig.set_size_inches(7.2, 5.2)
    plt.title("Q-Q plot of refined-model residuals")
    plt.xlabel("Theoretical quantiles")
    plt.ylabel("Standardized residual quantiles")
    save_current_figure("07_qq_plot.png")

    plt.figure(figsize=(7.2, 5.2))
    plt.scatter(predicted, residuals, color=TEAL, alpha=0.78, s=44)
    plt.axhline(0, color=GOLD, linewidth=2.1, linestyle="--")
    plt.xlabel("Fitted price (USD)")
    plt.ylabel("Residual (USD)")
    plt.title("Residuals versus fitted values")
    save_current_figure("08_residuals_vs_fitted.png")

    standard_effects = []
    for variable in selected:
        standard_effects.append(
            {
                "Variable": variable,
                "DollarEffectPerOneSD": float(
                    refined_model.params[variable] * main[variable].std(ddof=1)
                ),
                "pValue": float(refined_model.pvalues[variable]),
            }
        )
    standard_effects_frame = pd.DataFrame(standard_effects).sort_values(
        "DollarEffectPerOneSD", key=lambda series: series.abs(), ascending=True
    )
    standard_effects_frame.to_csv(
        OUTPUT_DIR / "standardized_effects.csv", index=False
    )
    plt.figure(figsize=(7.6, 4.6))
    colors = [TEAL if value >= 0 else RED for value in standard_effects_frame["DollarEffectPerOneSD"]]
    plt.barh(
        standard_effects_frame["Variable"],
        standard_effects_frame["DollarEffectPerOneSD"],
        color=colors,
    )
    plt.axvline(0, color="#6C7782", linewidth=1)
    plt.xlabel("Estimated price change for a one-SD increase (USD)")
    plt.title("Standardized effects in the refined model")
    save_current_figure("09_standardized_effects.png")

    return {
        "full_model": full_model,
        "refined_model": refined_model,
        "selected_variables": selected,
        "elimination_log": elimination_log,
        "vif": vif,
        "comparison": comparison,
        "diagnostics": diagnostics,
        "flagged_outliers": flagged,
        "standard_effects": standard_effects_frame,
        "cooks_threshold": cooks_threshold,
    }


def rank_markets_and_predict(
    main: pd.DataFrame, model_results: dict[str, object]
) -> tuple[pd.DataFrame, pd.DataFrame]:
    model = model_results["refined_model"]
    selected = model_results["selected_variables"]
    assert isinstance(selected, list)

    rankings = main.copy()
    ranking_x = sm.add_constant(rankings[selected], has_constant="add")
    rankings["PredictedMembershipPrice"] = model.predict(ranking_x)
    rankings["CompetitionPer100k"] = (
        rankings["CompetitorLocations"] / rankings["CountyPopulation"] * 100_000
    )
    rankings["LAFitnessPer100k"] = (
        rankings["LAFitnessLocations"] / rankings["CountyPopulation"] * 100_000
    )
    rankings["DemandComponent"] = minmax(np.log1p(rankings["CountyPopulation"]))
    rankings["PurchasingPowerComponent"] = minmax(
        rankings["MedianHouseholdIncome"]
    )
    rankings["LowCompetitionComponent"] = 1 - minmax(
        rankings["CompetitionPer100k"]
    )
    rankings["PricingComponent"] = minmax(rankings["PredictedMembershipPrice"])
    rankings["WhitespaceComponent"] = 1 - minmax(rankings["LAFitnessPer100k"])
    rankings["MarketPotentialScore"] = 100 * (
        0.30 * rankings["DemandComponent"]
        + 0.25 * rankings["PurchasingPowerComponent"]
        + 0.20 * rankings["LowCompetitionComponent"]
        + 0.15 * rankings["PricingComponent"]
        + 0.10 * rankings["WhitespaceComponent"]
    )
    rankings = rankings.sort_values(
        ["MarketPotentialScore", "CountyPopulation"], ascending=[False, False]
    ).reset_index(drop=True)
    rankings.insert(0, "Rank", np.arange(1, len(rankings) + 1))
    rankings.to_csv(OUTPUT_DIR / "expansion_rankings.csv", index=False)

    miami = main.loc[main["CountyName"].eq("Miami-Dade County")].iloc[0]
    target = rankings.iloc[0]
    scenarios = pd.DataFrame(
        [
            {
                "Scenario": "A - Rural, low competition",
                "CountyPopulation": 50_000,
                "LAFitnessLocations": 2,
                "CompetitorLocations": 1,
                "MedianHouseholdIncome": 62_000,
                "PopulationDensity": 120,
                "AvgGymRating": 4.20,
            },
            {
                "Scenario": "B - Miami-Dade, high competition",
                "CountyPopulation": 2_600_000,
                "LAFitnessLocations": 15,
                "CompetitorLocations": 30,
                "MedianHouseholdIncome": float(miami["MedianHouseholdIncome"]),
                "PopulationDensity": float(miami["PopulationDensity"]),
                "AvgGymRating": float(miami["AvgGymRating"]),
            },
            {
                "Scenario": f"C - Target market: {target['CountyName']}",
                **{variable: float(target[variable]) for variable in MODEL_VARIABLES},
            },
        ]
    )
    scenario_x = sm.add_constant(scenarios[selected], has_constant="add")
    prediction_frame = model.get_prediction(scenario_x).summary_frame(alpha=0.05)
    scenarios["PredictedPrice"] = prediction_frame["mean"].to_numpy()
    scenarios["MeanCI95Lower"] = prediction_frame["mean_ci_lower"].to_numpy()
    scenarios["MeanCI95Upper"] = prediction_frame["mean_ci_upper"].to_numpy()
    scenarios["PredictionInterval95Lower"] = prediction_frame["obs_ci_lower"].to_numpy()
    scenarios["PredictionInterval95Upper"] = prediction_frame["obs_ci_upper"].to_numpy()
    scenarios.to_csv(OUTPUT_DIR / "scenario_predictions.csv", index=False)

    configure_plot_style()
    top_ten = rankings.head(10).sort_values("MarketPotentialScore")
    plt.figure(figsize=(8.2, 5.7))
    bars = plt.barh(top_ten["CountyName"], top_ten["MarketPotentialScore"], color=TEAL)
    bars[-1].set_color(GOLD)
    plt.xlabel("Market potential score (0-100 within this dataset)")
    plt.title("Top simulated Florida expansion markets")
    plt.xlim(0, min(100, top_ten["MarketPotentialScore"].max() + 10))
    save_current_figure("10_top_markets.png")
    return rankings, scenarios


def write_report_payload(
    main: pd.DataFrame,
    summary: pd.DataFrame,
    correlation: pd.DataFrame,
    model_results: dict[str, object],
    rankings: pd.DataFrame,
    scenarios: pd.DataFrame,
    quality: pd.DataFrame,
) -> None:
    full_model = model_results["full_model"]
    refined_model = model_results["refined_model"]
    selected = model_results["selected_variables"]
    standard_effects = model_results["standard_effects"]
    strongest = standard_effects.iloc[
        standard_effects["DollarEffectPerOneSD"].abs().argmax()
    ]
    price_correlations = correlation["MembershipPrice"].drop("MembershipPrice")
    top_corr_variable = str(price_correlations.abs().idxmax())
    top_corr_value = float(price_correlations[top_corr_variable])

    payload = {
        "metadata": {
            "title": "Fitness Market Analysis: LA Fitness Expansion Strategy",
            "geography": "All 67 Florida counties",
            "random_seed": RANDOM_SEED,
            "data_mode": "Observed demographics and Google Places data plus estimated prices",
            "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
        },
        "dataset": {
            "rows": int(len(main)),
            "columns": int(len(main.columns)),
            "location_rows": int(pd.read_csv(DATA_DIR / "gym_locations.csv").shape[0]),
            "price_mean": float(main["MembershipPrice"].mean()),
            "price_median": float(main["MembershipPrice"].median()),
            "price_min": float(main["MembershipPrice"].min()),
            "price_max": float(main["MembershipPrice"].max()),
            "top_correlation_variable": top_corr_variable,
            "top_correlation_value": top_corr_value,
        },
        "models": {
            "full": {
                "r2": float(full_model.rsquared),
                "adjusted_r2": float(full_model.rsquared_adj),
                "aic": float(full_model.aic),
                "bic": float(full_model.bic),
                "rmse": float(np.sqrt(np.mean(full_model.resid**2))),
            },
            "refined": {
                "variables": selected,
                "r2": float(refined_model.rsquared),
                "adjusted_r2": float(refined_model.rsquared_adj),
                "aic": float(refined_model.aic),
                "bic": float(refined_model.bic),
                "rmse": float(np.sqrt(np.mean(refined_model.resid**2))),
            },
            "elimination_log": model_results["elimination_log"],
            "max_vif": float(model_results["vif"]["VIF"].max()),
            "max_vif_variable": str(
                model_results["vif"].loc[
                    model_results["vif"]["VIF"].idxmax(), "Variable"
                ]
            ),
            "strongest_standardized_effect": {
                "variable": str(strongest["Variable"]),
                "dollars_per_sd": float(strongest["DollarEffectPerOneSD"]),
                "p_value": float(strongest["pValue"]),
            },
        },
        "diagnostics": model_results["diagnostics"].to_dict(orient="records"),
        "outliers": model_results["flagged_outliers"].head(10).to_dict(
            orient="records"
        ),
        "top_five": rankings.head(5).to_dict(orient="records"),
        "scenarios": scenarios.to_dict(orient="records"),
        "summary_statistics": summary.reset_index(names="Variable").to_dict(
            orient="records"
        ),
        "quality_checks": quality.to_dict(orient="records"),
        "sources": SOURCE_ROWS,
    }
    (OUTPUT_DIR / "report_data.json").write_text(
        json.dumps(payload, indent=2), encoding="utf-8"
    )


def main() -> None:
    warnings.filterwarnings("ignore", category=FutureWarning)
    ensure_directories()
    pd.DataFrame(SOURCE_ROWS).to_csv(DATA_DIR / "data_sources.csv", index=False)
    demographics, demographic_internal = collect_demographics()
    locations = collect_google_places(demographic_internal)
    main_dataset, quality = build_main_dataset(demographics, locations)
    summary, correlation = create_eda_outputs(main_dataset)
    model_results = fit_models(main_dataset)
    rankings, scenarios = rank_markets_and_predict(main_dataset, model_results)
    write_report_payload(
        main_dataset,
        summary,
        correlation,
        model_results,
        rankings,
        scenarios,
        quality,
    )
    print(
        f"Completed analysis for {len(main_dataset)} counties; "
        f"collected {len(locations)} Google Places location records."
    )
    print(f"Refined predictors: {', '.join(model_results['selected_variables'])}")
    print(f"Top expansion market: {rankings.iloc[0]['CountyName']}")


if __name__ == "__main__":
    main()
