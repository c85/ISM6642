#!/usr/bin/env python3
"""Collect public, official membership-price observations for the tracked chains.

The output is intentionally a long observation file.  It keeps plan type,
billing frequency, one-time fees, annual fees, promotions, source URL, and
retrieval time separate so unlike offers are not silently treated as the same
price.  When a franchise's public enrollment page does not expose a price, the
collector records that fact; it never fills the gap with a synthetic value.
"""

from __future__ import annotations

import argparse
import csv
import html
import json
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode, urljoin
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
LOCATION_PATH = DATA_DIR / "gym_locations.csv"
LA_PRICING_PATH = DATA_DIR / "la_fitness_pricing.csv"
OUTPUT_PATH = DATA_DIR / "gym_membership_pricing.csv"
AUDIT_PATH = DATA_DIR / "pricing_collection_audit.csv"

USER_AGENT = "ISM6642-course-analysis/1.0 (public-data collection)"
YOUFIT_DIRECTORY = "https://youfit.com/locations/florida"
YOUFIT_JOIN_BASE = "https://join.youfit.com/"
YOUFIT_API_BASE = "https://jolapi.youfit.com/"
OTF_DETAILS_URL = "https://www.orangetheory.com/studio-details.json"
OTF_SEARCH_URL = "https://api.gateway.orangetheory.com/consumer-website/v1/locations/search"
OTF_PAGE_BASE = "https://www.orangetheory.com/en-us/locations/"
GOLDS_DIRECTORY = "https://www.goldsgym.com/locations/fl/"
PLANET_MEMBERSHIP_URL = "https://www.planetfitness.com/gym-memberships/"

CITY_COUNTY_OVERRIDES = {
    # The Census geocoder occasionally returns no match for this valid local
    # address even though its city-to-county relationship is unambiguous.
    "hollywood": "Broward County",
}

FIELDNAMES = [
    "GymChain",
    "ClubID",
    "GymName",
    "Address",
    "CountyName",
    "LocationScope",
    "PlanName",
    "PlanTerm",
    "PriceType",
    "DuesAmount",
    "DuesFrequency",
    "MonthlyEquivalent",
    "InitiationFee",
    "AnnualFee",
    "EffectiveMonthlyCost",
    "PromotionalDuesAmount",
    "PromotionStatus",
    "OfferExpiration",
    "Status",
    "SourceType",
    "SourceURL",
    "LocationURL",
    "RetrievedAtUTC",
    "Notes",
]


def fetch_text(url: str, *, timeout: int = 60) -> tuple[str, str]:
    for attempt in range(3):
        request = Request(
            url,
            headers={
                "User-Agent": USER_AGENT,
                "Accept": "text/html,application/json,application/javascript,*/*;q=0.8",
            },
        )
        try:
            with urlopen(request, timeout=timeout) as response:
                return response.geturl(), response.read().decode("utf-8", "ignore")
        except HTTPError as exc:
            if exc.code not in {429, 500, 502, 503, 504} or attempt == 2:
                raise
            time.sleep(2**attempt)
        except URLError:
            if attempt == 2:
                raise
            time.sleep(2**attempt)
    raise RuntimeError(f"Could not fetch {url}")


def fetch_json(url: str, *, timeout: int = 60) -> tuple[str, Any]:
    final_url, body = fetch_text(url, timeout=timeout)
    return final_url, json.loads(body)


def clean_html(value: str) -> str:
    value = re.sub(r"<br\s*/?>", "\n", value, flags=re.IGNORECASE)
    value = re.sub(r"<[^>]+>", " ", value)
    value = html.unescape(value).replace("\xa0", " ")
    return re.sub(r"\s+", " ", value).strip()


def as_float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    if isinstance(value, (int, float)):
        return float(value)
    match = re.search(r"-?[0-9][0-9,]*(?:\.[0-9]+)?", str(value))
    return float(match.group(0).replace(",", "")) if match else None


def amount(value: float | None) -> str | float:
    return "" if value is None else round(value, 2)


def zip_code(value: str) -> str:
    match = re.search(r"\b(\d{5})(?:-\d{4})?\b", value or "")
    return match.group(1) if match else ""


def monthly_equivalent(dues: float | None, frequency: str) -> float | None:
    if dues is None:
        return None
    normalized = frequency.casefold()
    if "bi-week" in normalized or "biweek" in normalized:
        return dues * 26 / 12
    if "week" in normalized:
        return dues * 52 / 12
    if "annual" in normalized or "year" in normalized:
        return dues / 12
    if "one-time" in normalized or "one time" in normalized:
        return None
    return dues


def first_year_cost(
    monthly: float | None,
    initiation: float | None,
    annual: float | None,
) -> float | None:
    if monthly is None:
        return None
    if initiation is None and annual is None:
        return monthly
    return monthly + (initiation or 0.0) / 12 + (annual or 0.0) / 12


def load_zip_county_map() -> dict[str, str]:
    """Use the existing exact-county Google observations as a ZIP crosswalk."""
    if not LOCATION_PATH.exists():
        return {}
    counties_by_zip: dict[str, set[str]] = {}
    with LOCATION_PATH.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            current_zip = zip_code(row.get("Address", ""))
            county = row.get("CountyName", "").strip()
            if current_zip and county:
                counties_by_zip.setdefault(current_zip, set()).add(county)
    return {
        current_zip: next(iter(counties))
        for current_zip, counties in counties_by_zip.items()
        if len(counties) == 1
    }


def census_geocoder_county(address: str) -> str:
    if not address:
        return ""
    params = urlencode(
        {
            "address": address,
            "benchmark": "Public_AR_Current",
            "vintage": "Current_Current",
            "format": "json",
        }
    )
    try:
        _, payload = fetch_json(
            "https://geocoding.geo.census.gov/geocoder/geographies/onelineaddress?"
            + params,
            timeout=45,
        )
        matches = payload.get("result", {}).get("addressMatches", [])
        counties = matches[0].get("geographies", {}).get("Counties", []) if matches else []
        return str(counties[0].get("NAME", "")).strip() if counties else ""
    except Exception:
        return ""


def county_for_address(
    address: str,
    zip_map: dict[str, str],
    geocoder_cache: dict[str, str],
) -> str:
    current_zip = zip_code(address)
    if current_zip in zip_map:
        return zip_map[current_zip]
    if address not in geocoder_cache:
        geocoder_cache[address] = census_geocoder_county(address)
    if geocoder_cache[address]:
        return geocoder_cache[address]
    parts = [part.strip().casefold() for part in address.split(",") if part.strip()]
    city = parts[-3] if len(parts) >= 3 else ""
    return CITY_COUNTY_OVERRIDES.get(city, "")


def empty_row(**values: Any) -> dict[str, Any]:
    row = {field: "" for field in FIELDNAMES}
    row.update(values)
    return row


def collect_la(rows: list[dict[str, Any]], retrieved_at: str) -> None:
    if not LA_PRICING_PATH.exists():
        rows.append(
            empty_row(
                GymChain="LA Fitness",
                LocationScope="Florida official club directory",
                Status="Source file missing",
                SourceType="Official LA Fitness signup collector",
                SourceURL="https://www.lafitness.com/Pages/MembershipSignUpSearch.aspx",
                RetrievedAtUTC=retrieved_at,
                Notes="Run collect_la_fitness_pricing.py first.",
            )
        )
        return
    with LA_PRICING_PATH.open(newline="", encoding="utf-8") as handle:
        la_rows = list(csv.DictReader(handle))
    for club in la_rows:
        try:
            plans = json.loads(club.get("Plans", "[]") or "[]")
        except json.JSONDecodeError:
            plans = []
        if not plans:
            rows.append(
                empty_row(
                    GymChain="LA Fitness",
                    ClubID=club.get("ClubID", ""),
                    GymName=club.get("OfficialClubName", ""),
                    Address=club.get("OfficialAddress", ""),
                    CountyName=club.get("CountyName", ""),
                    LocationScope="Official Florida club",
                    Status=club.get("Status", "No rate found"),
                    SourceType="Official LA Fitness membership signup flow",
                    SourceURL=club.get("SourceURL", ""),
                    RetrievedAtUTC=club.get("RetrievedAtUTC", retrieved_at),
                    Notes=club.get("Error", ""),
                )
            )
            continue
        for plan in plans:
            dues = as_float(plan.get("monthly_dues"))
            initiation = as_float(plan.get("initiation_fee"))
            annual = as_float(plan.get("annual_fee"))
            monthly = monthly_equivalent(dues, "Monthly")
            effective = as_float(plan.get("effective_monthly_cost"))
            rows.append(
                empty_row(
                    GymChain="LA Fitness",
                    ClubID=club.get("ClubID", ""),
                    GymName=club.get("OfficialClubName", ""),
                    Address=club.get("OfficialAddress", ""),
                    CountyName=club.get("CountyName", ""),
                    LocationScope="Official Florida club",
                    PlanName=plan.get("plan", ""),
                    PlanTerm="",
                    PriceType="Standard advertised dues",
                    DuesAmount=amount(dues),
                    DuesFrequency="Monthly",
                    MonthlyEquivalent=amount(monthly),
                    InitiationFee=amount(initiation),
                    AnnualFee=amount(annual),
                    EffectiveMonthlyCost=amount(effective),
                    Status="Observed",
                    SourceType="Official LA Fitness membership signup flow",
                    SourceURL=club.get("SourceURL", ""),
                    RetrievedAtUTC=club.get("RetrievedAtUTC", retrieved_at),
                    Notes=f"Access: {plan.get('access', '')}".strip(),
                )
            )


def discover_youfit_clubs() -> list[dict[str, str]]:
    _, directory = fetch_text(YOUFIT_DIRECTORY)
    join_links = re.findall(
        r"(?:data-src|src)=[\"'](https://join\.youfit\.com/[^\"']+)[\"']",
        directory,
        flags=re.IGNORECASE,
    )
    seed = join_links[0] if join_links else YOUFIT_JOIN_BASE + "miami-flagler-st"
    _, join_page = fetch_text(seed)
    asset_urls = [
        urljoin(seed, value)
        for value in re.findall(
            r"(?:src|href)=[\"']([^\"']+\.js(?:\?[^\"']*)?)[\"']",
            join_page,
            flags=re.IGNORECASE,
        )
    ]
    objects: dict[str, dict[str, str]] = {}
    for asset_url in dict.fromkeys(asset_urls):
        try:
            _, script = fetch_text(asset_url)
        except Exception:
            continue
        for club_number, original_name, club_name in re.findall(
            r'\{ClubNumber:(\d+),Original_ClubName:"([^"]+)",ClubName:"([^"]+)"\}',
            script,
        ):
            objects[club_number] = {
                "ClubNumber": club_number,
                "OriginalClubName": html.unescape(original_name),
                "ClubName": html.unescape(club_name),
            }
    return list(objects.values())


def collect_youfit(
    rows: list[dict[str, Any]],
    retrieved_at: str,
    zip_map: dict[str, str],
    geocoder_cache: dict[str, str],
    delay: float,
) -> None:
    try:
        clubs = discover_youfit_clubs()
    except Exception as exc:
        rows.append(
            empty_row(
                GymChain="YouFit",
                LocationScope="Official Florida directory",
                Status="Directory request failed",
                SourceType="Official YouFit enrollment app",
                SourceURL=YOUFIT_DIRECTORY,
                RetrievedAtUTC=retrieved_at,
                Notes=f"{type(exc).__name__}: {exc}",
            )
        )
        return

    florida_clubs = 0
    for index, club in enumerate(clubs, start=1):
        number = club["ClubNumber"]
        detail_url = YOUFIT_API_BASE + "api/Club/GetClubDetail?clubnumber=" + number
        plans_url = YOUFIT_API_BASE + "api/Plans/GetMemberShipPlan?clubnumber=" + number
        try:
            _, detail_payload = fetch_json(detail_url)
            detail = detail_payload.get("data") or {}
            if str(detail.get("club_state_abbr", "")).upper() != "FL":
                continue
            florida_clubs += 1
            address = ", ".join(
                part
                for part in [
                    detail.get("club_address_1", ""),
                    detail.get("club_city", ""),
                    detail.get("club_state_abbr", ""),
                    detail.get("club_postal", ""),
                ]
                if part
            )
            county = county_for_address(address, zip_map, geocoder_cache)
            _, plans_payload = fetch_json(plans_url)
            plans = plans_payload.get("data") or []
            location_url = YOUFIT_JOIN_BASE + club["ClubName"]
            if not plans:
                rows.append(
                    empty_row(
                        GymChain="YouFit",
                        ClubID=number,
                        GymName=detail.get("club_display_name") or detail.get("gyms_name") or club["OriginalClubName"],
                        Address=address,
                        CountyName=county,
                        LocationScope="Official Florida club",
                        Status="No rate found",
                        SourceType="Official YouFit enrollment API",
                        SourceURL=plans_url,
                        LocationURL=location_url,
                        RetrievedAtUTC=retrieved_at,
                    )
                )
            for plan in plans:
                dues = as_float(plan.get("schedulePreTaxAmount"))
                if dues is None:
                    dues = as_float(plan.get("planFeesPricisionValue"))
                frequency = str(plan.get("scheduleFrequency") or "")
                monthly = monthly_equivalent(dues, frequency)
                initiation = as_float(plan.get("initiationFee"))
                annual = None
                effective = first_year_cost(monthly, initiation, annual)
                notes = (
                    "Official YouFit enrollment API. "
                    f"clubFeeTotalAmount reported as {plan.get('clubFeeTotalAmount', '')}; "
                    "stored in notes rather than relabeled as an annual fee."
                )
                rows.append(
                    empty_row(
                        GymChain="YouFit",
                        ClubID=number,
                        GymName=detail.get("club_display_name") or detail.get("gyms_name") or club["OriginalClubName"],
                        Address=address,
                        CountyName=county,
                        LocationScope="Official Florida club",
                        PlanName=plan.get("marketingPlan") or plan.get("planName") or "",
                        PlanTerm=plan.get("planTerm") or "",
                        PriceType="Standard scheduled dues",
                        DuesAmount=amount(dues),
                        DuesFrequency=frequency,
                        MonthlyEquivalent=amount(monthly),
                        InitiationFee=amount(initiation),
                        AnnualFee=amount(annual),
                        EffectiveMonthlyCost=amount(effective),
                        PromotionStatus=plan.get("bannerText") or "",
                        Status="Observed" if dues is not None else "No rate found",
                        SourceType="Official YouFit enrollment API",
                        SourceURL=plans_url,
                        LocationURL=location_url,
                        RetrievedAtUTC=retrieved_at,
                        Notes=notes,
                    )
                )
        except Exception as exc:
            rows.append(
                empty_row(
                    GymChain="YouFit",
                    ClubID=number,
                    GymName=club["OriginalClubName"],
                    LocationScope="Official Florida club",
                    Status="Request failed",
                    SourceType="Official YouFit enrollment API",
                    SourceURL=plans_url,
                    RetrievedAtUTC=retrieved_at,
                    Notes=f"{type(exc).__name__}: {exc}",
                )
            )
        if index % 10 == 0:
            print(f"YouFit progress: {index}/{len(clubs)} app clubs", flush=True)
        time.sleep(max(0.0, delay))
    print(f"YouFit: {florida_clubs} Florida clubs returned by official API.", flush=True)


def parse_otf_products(page: str) -> list[dict[str, Any]]:
    products: list[dict[str, Any]] = []
    for raw in re.findall(r"studioProducts\.push\((\{.*?\})\);", page, flags=re.DOTALL):
        try:
            products.append(
                json.loads(raw.replace("\t", " ").replace("\r", " ").replace("\n", " "))
            )
        except json.JSONDecodeError:
            continue
    memberships = [
        product
        for product in products
        if str(product.get("product-type", "")).casefold() == "membership"
    ]
    preferred = [
        product
        for product in memberships
        if str(product.get("product-name", "")) in {"Basic", "Elite", "Premier"}
    ]
    return preferred or memberships


def collect_orangetheory(
    rows: list[dict[str, Any]],
    retrieved_at: str,
    zip_map: dict[str, str],
    geocoder_cache: dict[str, str],
    delay: float,
) -> None:
    try:
        _, detail_payload = fetch_json(OTF_DETAILS_URL)
        details = detail_payload.get("data") or []
    except Exception as exc:
        rows.append(
            empty_row(
                GymChain="Orangetheory Fitness",
                LocationScope="Official Florida studio directory",
                Status="Directory request failed",
                SourceType="Official Orangetheory studio directory",
                SourceURL=OTF_DETAILS_URL,
                RetrievedAtUTC=retrieved_at,
                Notes=f"{type(exc).__name__}: {exc}",
            )
        )
        return
    florida = [
        detail
        for detail in details
        if detail.get("locale") == "en-us"
        and str(detail.get("physicalState", "")).upper() == "FL"
        and detail.get("studioStatus") == "Active"
        and not detail.get("isDraft")
        and not detail.get("isArchived")
        and detail.get("environment") == "PROD"
        and re.fullmatch(r"\d{5}", str(detail.get("physicalPostalCode", "")))
        and "test" not in str(detail.get("name", "")).casefold()
    ]
    for index, detail in enumerate(florida, start=1):
        address = ", ".join(
            part
            for part in [
                detail.get("physicalAddress", ""),
                detail.get("physicalCity", ""),
                detail.get("physicalState", ""),
                detail.get("physicalPostalCode", ""),
            ]
            if part
        )
        county = county_for_address(address, zip_map, geocoder_cache)
        page_url = OTF_PAGE_BASE + str(detail.get("slug", ""))
        try:
            _, page = fetch_text(page_url)
            products = parse_otf_products(page)
            if not products:
                raise RuntimeError("No membership products were embedded in the official page.")
            for product in products:
                dues = as_float(product.get("default-price"))
                promotional = (
                    as_float(product.get("promotion-price"))
                    if str(product.get("promotion-status", "")).casefold() == "active"
                    else None
                )
                rows.append(
                    empty_row(
                        GymChain="Orangetheory Fitness",
                        ClubID=detail.get("locationNumber", ""),
                        GymName=detail.get("name", ""),
                        Address=address,
                        CountyName=county,
                        LocationScope="Official Florida studio",
                        PlanName=product.get("product-name", ""),
                        PlanTerm=product.get("product-name", ""),
                        PriceType="Standard advertised dues",
                        DuesAmount=amount(dues),
                        DuesFrequency="Monthly",
                        MonthlyEquivalent=amount(monthly_equivalent(dues, "Monthly")),
                        EffectiveMonthlyCost=amount(dues),
                        PromotionalDuesAmount=amount(promotional),
                        PromotionStatus=product.get("promotion-status", ""),
                        OfferExpiration=product.get("promotion-expiration-date", ""),
                        Status="Observed" if dues is not None else "No rate found",
                        SourceType="Official Orangetheory studio page",
                        SourceURL=page_url,
                        LocationURL=page_url,
                        RetrievedAtUTC=retrieved_at,
                        Notes="Prices are studio-specific and plan-specific; standard price retained even when a first-month promotion is active.",
                    )
                )
        except Exception as exc:
            rows.append(
                empty_row(
                    GymChain="Orangetheory Fitness",
                    ClubID=detail.get("locationNumber", ""),
                    GymName=detail.get("name", ""),
                    Address=address,
                    CountyName=county,
                    LocationScope="Official Florida studio",
                    Status="Request failed",
                    SourceType="Official Orangetheory studio page",
                    SourceURL=page_url,
                    LocationURL=page_url,
                    RetrievedAtUTC=retrieved_at,
                    Notes=f"{type(exc).__name__}: {exc}",
                )
            )
        if index % 10 == 0:
            print(f"Orangetheory progress: {index}/{len(florida)} Florida studios", flush=True)
        time.sleep(max(0.0, delay))
    print(f"Orangetheory: {len(florida)} active Florida studios discovered.", flush=True)


def extract_gold_amount(section: str) -> float | None:
    patterns = [
        r"<p>\s*\$\s*</p>\s*<p[^>]*>\s*(\d+)\s*</p>\s*<sup[^>]*>\s*(\d{2})\s*</sup>",
        r"<span[^>]*>\$\s*</span>.*?<span[^>]*>\s*(\d+)\s*</span>.*?<span[^>]*>\s*\.\s*(\d{2})\s*</span>",
    ]
    for pattern in patterns:
        match = re.search(pattern, section, flags=re.IGNORECASE | re.DOTALL)
        if match:
            return float(f"{match.group(1)}.{match.group(2)}")
    return None


def parse_gleantap_plans(page: str) -> list[dict[str, Any]]:
    full_text = clean_html(page)
    annual_match = re.search(r"carry a \$([0-9]+(?:\.[0-9]{2})?) annual fee", full_text, re.I)
    annual_fee = as_float(annual_match.group(1)) if annual_match else None
    enrollment_fee = 0.0 if re.search(r"\$0\s+(?:enrollment|ENROLLMENT)", full_text, re.I) else None
    sections = re.findall(
        r'<section\s+class="plans-card[^>]*>.*?</section>', page, flags=re.IGNORECASE | re.DOTALL
    )
    plans: list[dict[str, Any]] = []
    for section in sections:
        title_match = re.search(r"<h2[^>]*>(.*?)</h2>", section, flags=re.I | re.S)
        title = clean_html(title_match.group(1)) if title_match else "Gold's Gym advertised plan"
        dues = extract_gold_amount(section)
        visible = clean_html(section)
        if dues is None:
            continue
        if re.search(r"one-time", visible, re.I):
            frequency = "One-Time"
            months_match = re.search(r"(\d+)\s+months? of access", visible, re.I)
            monthly = dues / float(months_match.group(1)) if months_match else None
            annual = 0.0
        elif re.search(r"bi-?weekly", visible, re.I):
            frequency = "Bi-Weekly"
            monthly = monthly_equivalent(dues, frequency)
            annual = annual_fee
        elif re.search(r"monthly", visible, re.I):
            frequency = "Monthly"
            monthly = dues
            annual = annual_fee
        else:
            frequency = ""
            monthly = None
            annual = None
        plans.append(
            {
                "title": title,
                "dues": dues,
                "frequency": frequency,
                "monthly": monthly,
                "annual": annual,
                "initiation": enrollment_fee,
            }
        )
    return plans


def parse_gasworx_plans(page: str) -> list[dict[str, Any]]:
    plans: list[dict[str, Any]] = []
    for index, match in enumerate(
        re.finditer(r"then\s+\$([0-9]+(?:\.[0-9]{2})?)\s*/\s*(bi-?weekly|month)", page, re.I),
        start=1,
    ):
        dues = as_float(match.group(1))
        frequency = "Bi-Weekly" if "week" in match.group(2).casefold() else "Monthly"
        monthly = monthly_equivalent(dues, frequency)
        plans.append(
            {
                "title": f"Gas Worx advertised plan {index}",
                "dues": dues,
                "frequency": frequency,
                "monthly": monthly,
                "annual": None,
                "initiation": None,
            }
        )
    return plans


def parse_gold_location_page(page: str) -> tuple[str, str]:
    address_match = re.search(r"data-address=[\"']([^\"']+)[\"']", page, flags=re.I)
    address = html.unescape(address_match.group(1)) if address_match else ""
    join_match = re.search(r"data-button-link=[\"']([^\"']+)[\"']", page, flags=re.I)
    if not join_match:
        join_match = re.search(
            r"href=[\"'](https?://(?:secure\.peakpayment\.com|pages\.gleantap\.org|onlinejoin\.abcfitness\.com|goldsgymgasworx\.com)[^\"']+)[\"']",
            page,
            flags=re.I,
        )
    join_url = html.unescape(join_match.group(1)) if join_match else ""
    return address, join_url


def collect_gold(
    rows: list[dict[str, Any]],
    retrieved_at: str,
    zip_map: dict[str, str],
    geocoder_cache: dict[str, str],
    delay: float,
) -> None:
    try:
        _, directory = fetch_text(GOLDS_DIRECTORY)
        location_urls = list(
            dict.fromkeys(
                re.findall(r"https://www\.goldsgym\.com/locations/fl/[^\"'< ]+/", directory, re.I)
            )
        )
        location_urls = [
            url
            for url in location_urls
            if url.rstrip("/").rsplit("/", 1)[-1].casefold() != "feed"
        ]
    except Exception as exc:
        rows.append(
            empty_row(
                GymChain="Gold's Gym",
                LocationScope="Official Florida directory",
                Status="Directory request failed",
                SourceType="Official Gold's Gym Florida directory",
                SourceURL=GOLDS_DIRECTORY,
                RetrievedAtUTC=retrieved_at,
                Notes=f"{type(exc).__name__}: {exc}",
            )
        )
        return

    for index, location_url in enumerate(location_urls, start=1):
        try:
            _, location_page = fetch_text(location_url)
            address, join_url = parse_gold_location_page(location_page)
            slug = location_url.rstrip("/").rsplit("/", 1)[-1]
            if not address:
                address = slug.replace("-", " ").title() + ", FL"
            county = county_for_address(address, zip_map, geocoder_cache)
            if not join_url:
                raise RuntimeError("Official location page did not expose a join URL.")
            _, join_page = fetch_text(join_url)
            if "pages.gleantap.org" in join_url:
                plans = parse_gleantap_plans(join_page)
            elif "goldsgymgasworx.com" in join_url:
                plans = parse_gasworx_plans(join_page)
            else:
                plans = []
            if plans:
                for plan in plans:
                    rows.append(
                        empty_row(
                            GymChain="Gold's Gym",
                            ClubID=slug,
                            GymName=f"Gold's Gym - {slug.replace('-', ' ').title()}",
                            Address=address,
                            CountyName=county,
                            LocationScope="Official Florida club",
                            PlanName=plan["title"],
                            PlanTerm=plan["title"],
                            PriceType="Standard advertised dues",
                            DuesAmount=amount(plan["dues"]),
                            DuesFrequency=plan["frequency"],
                            MonthlyEquivalent=amount(plan["monthly"]),
                            InitiationFee=amount(plan["initiation"]),
                            AnnualFee=amount(plan["annual"]),
                            EffectiveMonthlyCost=amount(
                                first_year_cost(plan["monthly"], plan["initiation"], plan["annual"])
                            ),
                            PromotionStatus="August 2026 offer" if "August" in clean_html(join_page) else "",
                            Status="Observed",
                            SourceType="Official Gold's Gym local enrollment page",
                            SourceURL=join_url,
                            LocationURL=location_url,
                            RetrievedAtUTC=retrieved_at,
                            Notes="Franchise-specific offer; prices shown before tax where stated.",
                        )
                    )
            else:
                rows.append(
                    empty_row(
                        GymChain="Gold's Gym",
                        ClubID=slug,
                        GymName=f"Gold's Gym - {slug.replace('-', ' ').title()}",
                        Address=address,
                        CountyName=county,
                        LocationScope="Official Florida club",
                        Status="No public rate found",
                        SourceType="Official Gold's Gym local enrollment page",
                        SourceURL=join_url,
                        LocationURL=location_url,
                        RetrievedAtUTC=retrieved_at,
                        Notes="The official enrollment endpoint was reachable but did not expose a parseable public price.",
                    )
                )
        except Exception as exc:
            rows.append(
                empty_row(
                    GymChain="Gold's Gym",
                    ClubID=location_url.rstrip("/").rsplit("/", 1)[-1],
                    LocationScope="Official Florida club",
                    Status="Request failed",
                    SourceType="Official Gold's Gym local enrollment page",
                    SourceURL=location_url,
                    RetrievedAtUTC=retrieved_at,
                    Notes=f"{type(exc).__name__}: {exc}",
                )
            )
        if index % 2 == 0:
            print(f"Gold's Gym progress: {index}/{len(location_urls)} official Florida clubs", flush=True)
        time.sleep(max(0.0, delay))
    print(f"Gold's Gym: {len(location_urls)} official Florida clubs discovered.", flush=True)


def add_planet_baseline(rows: list[dict[str, Any]], retrieved_at: str) -> None:
    """Record the official chain floor without pretending it is local county data."""
    for plan_name, dues in (("Classic", 15.00), ("PF Black Card", 24.99)):
        rows.append(
            empty_row(
                GymChain="Planet Fitness",
                GymName="Planet Fitness - official published starting rate",
                LocationScope="Chainwide published floor (not county-specific)",
                PlanName=plan_name,
                PriceType="Official published starting rate",
                DuesAmount=dues,
                DuesFrequency="Monthly",
                MonthlyEquivalent=dues,
                AnnualFee=49.00,
                EffectiveMonthlyCost=dues + 49.00 / 12,
                Status="Observed published baseline",
                SourceType="Official Planet Fitness membership page",
                SourceURL=PLANET_MEMBERSHIP_URL,
                RetrievedAtUTC=retrieved_at,
                Notes="Planet Fitness states that prices vary by location; this is a chainwide starting floor and is excluded from county averages.",
            )
        )


def build_audit(rows: list[dict[str, Any]], retrieved_at: str) -> list[dict[str, Any]]:
    audit: list[dict[str, Any]] = []
    for chain in [
        "LA Fitness",
        "Planet Fitness",
        "YouFit",
        "Gold's Gym",
        "Orangetheory Fitness",
    ]:
        chain_rows = [row for row in rows if row["GymChain"] == chain]
        observed = [row for row in chain_rows if str(row["Status"]).startswith("Observed")]
        local = [row for row in observed if row["CountyName"]]
        audit.append(
            {
                "GymChain": chain,
                "RowsWritten": len(chain_rows),
                "ObservedPriceRows": len(observed),
                "ObservedLocalPriceRows": len(local),
                "DistinctLocalClubs": len({row["ClubID"] for row in local if row["ClubID"]}),
                "DistinctCountiesWithObservedPrice": len({row["CountyName"] for row in local}),
                "NonObservedRows": len(chain_rows) - len(observed),
                "RetrievedAtUTC": retrieved_at,
                "Notes": "Local advertised rates only; blank or non-observed rows document source coverage and are not imputed here.",
            }
        )
    return audit


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--delay", type=float, default=0.08, help="Seconds between source requests")
    parser.add_argument("--output", type=Path, default=OUTPUT_PATH)
    parser.add_argument("--audit-output", type=Path, default=AUDIT_PATH)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.audit_output.parent.mkdir(parents=True, exist_ok=True)
    retrieved_at = datetime.now(timezone.utc).isoformat()
    zip_map = load_zip_county_map()
    geocoder_cache: dict[str, str] = {}
    rows: list[dict[str, Any]] = []

    collect_la(rows, retrieved_at)
    add_planet_baseline(rows, retrieved_at)
    collect_youfit(rows, retrieved_at, zip_map, geocoder_cache, args.delay)
    collect_gold(rows, retrieved_at, zip_map, geocoder_cache, args.delay)
    collect_orangetheory(rows, retrieved_at, zip_map, geocoder_cache, args.delay)

    with args.output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)
    audit = build_audit(rows, retrieved_at)
    with args.audit_output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(audit[0].keys()))
        writer.writeheader()
        writer.writerows(audit)

    print(f"Wrote {len(rows)} membership-price rows to {args.output}.", file=sys.stderr)
    for item in audit:
        print(
            f"{item['GymChain']}: {item['ObservedLocalPriceRows']} local observed price rows, "
            f"{item['DistinctCountiesWithObservedPrice']} counties",
            file=sys.stderr,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
