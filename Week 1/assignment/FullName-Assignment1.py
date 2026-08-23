"""Assignment 1: Laptop Price Prediction."""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import statsmodels.api as sm
from statsmodels.stats.outliers_influence import variance_inflation_factor

# The script saves figures instead of opening interactive plot windows.
plt.switch_backend("Agg")


# File locations
BASE_DIR = Path(__file__).resolve().parent
DATA_PATH = BASE_DIR / "LaptopSalesJanuary2008.csv"
OUTPUT_DIR = BASE_DIR / "outputs"

# Column names used throughout the analysis
PRICE = "Retail Price"
CONFIGURATION = "Configuration"
HD_SIZE = "HD Size (GB)"
RAM = "RAM (GB)"
BATTERY = "Battery Life (Hours)"
PROCESSOR = "Processor Speeds (GHz)"
WIRELESS = "Integrated Wireless?"
APPLICATIONS = "Bundled Applications?"

PHASE1_FEATURES = [HD_SIZE]
PHASE2_FEATURES = [HD_SIZE, RAM, BATTERY]


# -----------------------------------------------------------------------------
# Data ingestion and preprocessing
# -----------------------------------------------------------------------------
def load_data(filepath):
    """Load the CSV and check that the assignment columns are available."""
    required_columns = [
        PRICE,
        CONFIGURATION,
        HD_SIZE,
        RAM,
        BATTERY,
        PROCESSOR,
        WIRELESS,
        APPLICATIONS,
    ]

    if not filepath.exists():
        raise FileNotFoundError(f"Dataset not found: {filepath}")

    df = pd.read_csv(filepath)
    missing_columns = [column for column in required_columns if column not in df]
    if missing_columns:
        raise ValueError(f"Missing required columns: {missing_columns}")

    print("\n--- data ingestion ---")
    print(f"Rows: {len(df):,}")
    print(f"Columns: {len(df.columns)}")
    print(f"Unique configurations: {df[CONFIGURATION].nunique()}")
    print("\nMissing values in assignment columns:")
    print(df[required_columns].isna().sum().to_string())
    return df


def prepare_data(df, features):
    """Keep complete rows for a model and convert its variables to numbers."""
    columns = [PRICE, CONFIGURATION, *features]
    model_data = df[columns].copy()

    for column in [PRICE, *features]:
        model_data[column] = pd.to_numeric(model_data[column], errors="coerce")

    rows_before = len(model_data)
    model_data = model_data.dropna()
    rows_dropped = rows_before - len(model_data)
    if rows_dropped:
        print(f"Dropped {rows_dropped:,} incomplete rows for {features}.")

    return model_data


def fit_model(data, features):
    """Fit an ordinary least squares regression with an intercept."""
    X = sm.add_constant(data[features], has_constant="add")
    return sm.OLS(data[PRICE], X).fit()


def save_figure(fig, filename):
    """Save a figure that can be inserted into the executive summary."""
    OUTPUT_DIR.mkdir(exist_ok=True)
    output_path = OUTPUT_DIR / filename
    fig.savefig(output_path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved figure: {output_path.name}")


def format_p_value(p_value):
    """Display very small p-values without rounding them to zero."""
    return "< 0.001" if p_value < 0.001 else f"{p_value:.4f}"


# -----------------------------------------------------------------------------
# Phase 1: simple linear regression
# -----------------------------------------------------------------------------
def phase1_eda(data, model):
    """Plot retail price against storage, including the fitted regression line."""
    line_x = np.linspace(data[HD_SIZE].min(), data[HD_SIZE].max(), 200)
    line_data = pd.DataFrame({"const": 1.0, HD_SIZE: line_x})

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.scatter(data[HD_SIZE], data[PRICE], alpha=0.2, s=18, label="Sales")
    ax.plot(
        line_x,
        model.predict(line_data),
        color="firebrick",
        linewidth=2.5,
        label="Fitted regression line",
    )
    ax.set_xlabel("Hard Drive Size (GB)")
    ax.set_ylabel("Retail Price ($)")
    ax.set_title("Retail Price vs. Hard Drive Size")
    ax.legend()
    fig.tight_layout()
    save_figure(fig, "phase1_price_vs_storage.png")


def evaluate_phase1_model(model):
    """Report Phase 1 statistics and their business meaning."""
    coefficient = model.params[HD_SIZE]
    r_squared = model.rsquared
    p_value = model.pvalues[HD_SIZE]

    print("\n--- phase 1: simple linear regression ---")
    print("H0: Hard-drive size has no linear relationship with retail price.")
    print("H1: Larger hard drives are associated with higher retail prices.")
    print(
        f"Regression equation: Price = {model.params['const']:.4f} "
        f"+ {coefficient:.4f}(HD Size)"
    )
    print(f"R-squared: {r_squared:.4f}")
    print(f"P-value for HD Size: {format_p_value(p_value)}")
    print(
        f"Each additional 100 GB is associated with a ${coefficient * 100:,.2f} "
        "increase in predicted price."
    )
    print(
        f"Storage explains {r_squared:.1%} of price variation. It is statistically "
        "significant, but it is not a strong standalone predictor."
    )


# -----------------------------------------------------------------------------
# Phase 2: multiple linear regression
# -----------------------------------------------------------------------------
def phase2_eda(data):
    """Plot each Phase 2 predictor against retail price."""
    fig, axes = plt.subplots(1, 3, figsize=(15, 4.5))

    for ax, feature in zip(axes, PHASE2_FEATURES):
        ax.scatter(data[feature], data[PRICE], alpha=0.2, s=15)
        ax.set_xlabel(feature)
        ax.set_ylabel("Retail Price ($)")
        ax.set_title(f"Price vs. {feature}")

    fig.suptitle("Phase 2 Predictor Relationships", fontsize=14)
    fig.tight_layout()
    save_figure(fig, "phase2_predictor_relationships.png")


def check_multicollinearity(data):
    """Check predictor correlations and variance inflation factors (VIFs)."""
    predictors = data[PHASE2_FEATURES].astype(float)
    X = sm.add_constant(predictors, has_constant="add")

    vif_results = pd.DataFrame(
        {
            "Predictor": PHASE2_FEATURES,
            "VIF": [
                variance_inflation_factor(X.to_numpy(), column_number)
                for column_number in range(1, X.shape[1])
            ],
        }
    )

    print("\n--- phase 2: predictor correlations ---")
    print(predictors.corr().round(3).to_string())
    print("\n--- phase 2: variance inflation factors ---")
    print(vif_results.to_string(index=False, formatters={"VIF": "{:.3f}".format}))

    if vif_results["VIF"].max() < 5:
        print("All VIFs are below 5, so multicollinearity is not a concern.")
    else:
        print("At least one VIF is 5 or higher and should be investigated.")


def evaluate_phase2_model(model1, model2):
    """Compare the two models and interpret the Phase 2 coefficients."""
    print("\n--- phase 2: multiple linear regression ---")
    print(f"Model 1 adjusted R-squared: {model1.rsquared_adj:.4f}")
    print(f"Model 2 adjusted R-squared: {model2.rsquared_adj:.4f}")
    print(
        f"Improvement in adjusted R-squared: "
        f"{model2.rsquared_adj - model1.rsquared_adj:.4f}"
    )

    descriptions = {
        HD_SIZE: "one additional GB of storage",
        RAM: "one additional GB of RAM",
        BATTERY: "one additional hour of battery life",
    }

    print("\nCoefficients, holding the other variables constant:")
    negative_features = []
    for feature in PHASE2_FEATURES:
        coefficient = model2.params[feature]
        print(
            f"- {descriptions[feature]}: ${coefficient:,.2f}; "
            f"p-value {format_p_value(model2.pvalues[feature])}"
        )
        if coefficient < 0:
            negative_features.append(feature)

    if negative_features:
        print(f"Counterintuitive negative coefficients: {', '.join(negative_features)}")
    else:
        print("There are no counterintuitive signs; all three coefficients are positive.")

    print(
        f"Model 2 explains {model2.rsquared_adj:.1%} of adjusted price variation, "
        "so it is more useful for pricing decisions within the observed data range."
    )


def save_model_diagnostics(model1, model2):
    """Save residual plots for both required models."""
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.5))

    for ax, model, title in zip(
        axes,
        [model1, model2],
        ["Model 1", "Model 2"],
    ):
        ax.scatter(model.fittedvalues, model.resid, alpha=0.2, s=15)
        ax.axhline(0, color="firebrick", linestyle="--")
        ax.set_xlabel("Fitted Retail Price ($)")
        ax.set_ylabel("Residual ($)")
        ax.set_title(title)

    fig.suptitle("Regression Diagnostics: Residuals vs. Fitted Values", fontsize=14)
    fig.tight_layout()
    save_figure(fig, "regression_diagnostics.png")


# -----------------------------------------------------------------------------
# Phase 3: required forecasts
# -----------------------------------------------------------------------------
def make_forecast(model, values):
    """Return a point forecast and a 95% prediction interval."""
    new_laptop = pd.DataFrame([values])
    new_laptop = sm.add_constant(new_laptop, has_constant="add")
    result = model.get_prediction(new_laptop).summary_frame(alpha=0.05).iloc[0]
    return result


def print_range_warnings(training_data, values):
    """Warn when a requested specification is outside the training range."""
    outside_range = False

    for feature, requested_value in values.items():
        minimum = training_data[feature].min()
        maximum = training_data[feature].max()
        if requested_value < minimum or requested_value > maximum:
            outside_range = True
            print(
                f"WARNING: {feature} request is {requested_value:g}; "
                f"training range is {minimum:g}-{maximum:g}."
            )

    return outside_range


def predict_model1(model, training_data):
    """Forecast a laptop price using 2,000 GB of storage."""
    values = {HD_SIZE: 2000}
    forecast = make_forecast(model, values)

    print("\n--- phase 3: Model 1 forecast ---")
    print(f"Predicted price: ${forecast['mean']:,.2f}")
    print(
        f"95% prediction interval: ${forecast['obs_ci_lower']:,.2f} to "
        f"${forecast['obs_ci_upper']:,.2f}"
    )
    print_range_warnings(training_data, values)
    return forecast


def predict_model2(model, training_data):
    """Forecast using 2,000 GB storage, 44 GB RAM, and four-hour battery life."""
    values = {HD_SIZE: 2000, RAM: 44, BATTERY: 4}
    forecast = make_forecast(model, values)

    print("\n--- phase 3: Model 2 forecast ---")
    print(f"Predicted price: ${forecast['mean']:,.2f}")
    print(
        f"95% prediction interval: ${forecast['obs_ci_lower']:,.2f} to "
        f"${forecast['obs_ci_upper']:,.2f}"
    )
    print_range_warnings(training_data, values)
    return forecast


def compare_predictions(model1_forecast, model2_forecast, model1, model2):
    """Compare the forecasts and explain which model deserves more confidence."""
    difference = model2_forecast["mean"] - model1_forecast["mean"]

    print("\n--- phase 3: forecast comparison ---")
    print(f"Model 1 prediction: ${model1_forecast['mean']:,.2f}")
    print(f"Model 2 prediction: ${model2_forecast['mean']:,.2f}")
    print(f"Difference: ${difference:,.2f}")
    print(
        f"Model 2 is stronger within the observed data because its adjusted "
        f"R-squared is {model2.rsquared_adj:.3f}, compared with "
        f"{model1.rsquared_adj:.3f} for Model 1."
    )
    print(
        "However, neither specific forecast is dependable because 2,000 GB of "
        "storage and 44 GB of RAM are far outside the training ranges. The "
        "prediction intervals do not remove that extrapolation risk."
    )


# -----------------------------------------------------------------------------
# Phase 3: model optimization
# -----------------------------------------------------------------------------
def optimize_model(df):
    """Compare feature sets on one configuration-aware train/test split."""
    columns = [
        PRICE,
        CONFIGURATION,
        HD_SIZE,
        RAM,
        BATTERY,
        PROCESSOR,
        WIRELESS,
        APPLICATIONS,
    ]
    model_data = df[columns].dropna().copy()

    # Convert the two Yes/No product options into model-ready numeric features.
    model_data["Wireless Included"] = model_data[WIRELESS].map({"No": 0, "Yes": 1})
    model_data["Applications Included"] = model_data[APPLICATIONS].map(
        {"No": 0, "Yes": 1}
    )

    feature_sets = {
        "HD only": [HD_SIZE],
        "Phase 2 model": [HD_SIZE, RAM, BATTERY],
        "Expanded hardware model": [HD_SIZE, RAM, BATTERY, PROCESSOR],
        "Full product model": [
            HD_SIZE,
            RAM,
            BATTERY,
            PROCESSOR,
            "Wireless Included",
            "Applications Included",
        ],
    }

    # Split by configuration so the same laptop configuration cannot appear in
    # both the training and test sets.
    configurations = model_data[CONFIGURATION].unique().copy()
    random_generator = np.random.default_rng(42)
    random_generator.shuffle(configurations)
    test_count = int(np.ceil(len(configurations) * 0.20))
    test_configurations = configurations[:test_count]

    test_mask = model_data[CONFIGURATION].isin(test_configurations)
    train_data = model_data.loc[~test_mask]
    test_data = model_data.loc[test_mask]

    results = []
    for model_name, features in feature_sets.items():
        model = fit_model(train_data, features)
        X_test = sm.add_constant(test_data[features], has_constant="add")
        predictions = model.predict(X_test)
        mse = np.mean((test_data[PRICE] - predictions) ** 2)

        results.append(
            {
                "Model": model_name,
                "Features": features,
                "Test MSE": mse,
                "Training Adjusted R-Squared": model.rsquared_adj,
            }
        )
    best_result = min(results, key=lambda result: result["Test MSE"])
    best_features = best_result["Features"]

    # Refit the selected model on all available rows after model selection.
    final_model = fit_model(model_data, best_features)

    print("\n--- phase 3: model optimization ---")
    print(
        f"Training configurations: {train_data[CONFIGURATION].nunique()}; "
        f"test configurations: {test_data[CONFIGURATION].nunique()}"
    )

    for result in results:
        print(f"\nModel: {result['Model']}")
        print(f"Features: {result['Features']}")
        print(f"Test MSE: {result['Test MSE']:.2f}")
        print(
            f"Training adjusted R-squared: "
            f"{result['Training Adjusted R-Squared']:.4f}"
        )

    print("\nSelected model:")
    print(f"{best_result['Model']} with a test MSE of {best_result['Test MSE']:.2f}")
    print(f"The final model was refit using all {len(model_data):,} complete rows.")
    print(
        "The product options were engineered from Yes/No values into 1/0 values. "
        "Configuration was used only to create a fair split, not as a predictor."
    )

    # Save the MSE comparison for the executive summary.
    fig, ax = plt.subplots(figsize=(9, 5))
    names = [result["Model"] for result in results]
    mses = [result["Test MSE"] for result in results]
    ax.bar(names, mses, color="#4C78A8")
    ax.set_ylabel("Test Mean Squared Error")
    ax.set_title("Model Optimization Results (Lower Is Better)")
    ax.tick_params(axis="x", rotation=20)
    fig.tight_layout()
    save_figure(fig, "phase3_model_optimization.png")

    return final_model, best_features, results


# -----------------------------------------------------------------------------
# Main program
# -----------------------------------------------------------------------------
def main():
    """Run all assignment phases in order."""
    df = load_data(DATA_PATH)

    # Phase 1
    phase1_data = prepare_data(df, PHASE1_FEATURES)
    model1 = fit_model(phase1_data, PHASE1_FEATURES)
    phase1_eda(phase1_data, model1)
    evaluate_phase1_model(model1)

    # Phase 2
    phase2_data = prepare_data(df, PHASE2_FEATURES)
    phase2_eda(phase2_data)
    check_multicollinearity(phase2_data)
    model2 = fit_model(phase2_data, PHASE2_FEATURES)
    evaluate_phase2_model(model1, model2)
    save_model_diagnostics(model1, model2)

    # Phase 3
    model1_forecast = predict_model1(model1, phase1_data)
    model2_forecast = predict_model2(model2, phase2_data)
    compare_predictions(model1_forecast, model2_forecast, model1, model2)
    optimize_model(df)

    print(f"\nAnalysis complete. Figures were saved to: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
