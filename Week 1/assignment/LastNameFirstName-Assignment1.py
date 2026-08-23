# import
import pandas as pd
import matplotlib.pyplot as plt
import statsmodels.api as sm
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error

#data ingestion
def load_data(filepath):
    """
    load the laptop sales csv file into a pandas dataframe.
    """
    df = pd.read_csv(filepath)

    print("\n--- data preview ---")
    print(df.head())

    print("\n--- columns ---")
    print(df.columns)

    return df


# data processing
def preprocess_data(df):
    """
    inspect the dataset for missing values and verify that the
    variables used in Phase 1 are usable for regression.
    """

    print("\n--- data types ---")
    print(df.dtypes)

    print("\n--- missing values ---")
    print(df.isnull().sum())

    # keep rows where both Phase 1 variables are present
    phase1_data = df[["HD Size (GB)", "Retail Price"]].dropna()

    print("\n--- phase 1 stats ---")
    print(phase1_data.describe())

    return phase1_data

# phase 1
def phase1_eda(df):
    """
    Explore the relationship between hard drive size and retail price.
    """

    x = df["HD Size (GB)"]
    y = df["Retail Price"]

    plt.scatter(x, y)

    plt.xlabel("Hard Drive Size (GB)")
    plt.ylabel("Retail Price ($)")
    plt.title("Retail Price vs. Hard Drive Size")

    plt.show()

    # eda observation:
    # the scatterplot shows a general upward trend, meaning that larger hard
    # drives tend to be associated with higher retail prices
    # however, retail price can vary considerably even when the hard drive
    # size remains the same. this suggests that storage capacity alone
    # does not fully explain laptop price


# phase 1 - modeling
def build_phase1_model(df):
    """
    build a simple linear regression model using hd size (gb)
    to predict retail price
    """

    x = df["HD Size (GB)"]
    y = df["Retail Price"]

    # add a constant so the model can estimate the intercept.
    X = sm.add_constant(x)

    # ols regression.
    model1 = sm.OLS(y, X).fit()
    return model1

# phase 1 - model evaluation
def evaluate_phase1_model(model):
    """
    Eealuate the hhase 1 regression model using the coefficient,
    r-squared, and p-value.
    """

    print("\n--- phase 1 regression results ---")
    print(model.summary())

    coefficient = model.params["HD Size (GB)"]
    intercept = model.params["const"]
    r_squared = model.rsquared
    p_value = model.pvalues["HD Size (GB)"]

    print("\n--- phase 1 key results ---")
    print(f"Intercept: {intercept:.4f}")
    print(f"HD Size Coefficient: {coefficient:.4f}")
    print(f"R-squared: {r_squared:.4f}")
    print(f"P-value: {p_value:.6f}")

    """
    PHASE 1 INTERPRETATION

    Business Hypothesis:

    H0:
    Hard drive size has no statistically significant linear
    relationship with retail price.

    H1:
    Larger hard drive sizes are associated with higher retail prices.


    Regression Equation:
    Retail Price = 444.0708 + 0.2917(HD Size)


    Coefficient:
    The coefficient for HD Size is approximately 0.2917.
    This means that each additional 1 GB of hard drive storage is
    associated with approximately a $0.29 increase in predicted
    retail price.

    An additional 100 GB is therefore associated with approximately:
    100 * 0.2917 = $29.17
    higher predicted retail price.


    R-Squared:
    R^2 = 0.236

    Hard drive size explains approximately 23.6% of the variation
    in retail price.

    The remaining 76.4% of variation is not explained by this
    one-variable model. This suggests that other variables or sources
    of variation also influence retail price.

    P-Value:
    The p-value for HD Size is extremely small and is displayed
    as 0.000 in the statsmodels output.

    Therefore:
    p < 0.001
    Since this is below the commonly used significance level of 0.05,
    the null hypothesis is rejected.

    There is strong statistical evidence that hard drive size has a
    positive linear relationship with retail price.


    Important Distinction:
    The p-value tells us whether there is statistical evidence that
    the relationship exists.

    R-squared tells us how much of the variation in retail price is
    explained by the model.

    In this case, hard drive size is statistically significant, but
    it is not a strong standalone predictor because it explains only
    about 23.6% of price variation.

    Business Conclusion:
    Larger hard drive sizes are generally associated with higher
    laptop retail prices.
    However, storage capacity alone does not explain most of the
    variation in price.
    This motivates Phase 2, where additional laptop specifications
    will be included in the model to determine whether predictive
    performance improves.
    """

# phase 2 - data preparation
def prepare_phase2_data(df):
    """
    prepare the variables used for the multivariate regression model
    """

    phase2_columns = [
        "Retail Price",
        "HD Size (GB)",
        "RAM (GB)",
        "Battery Life (Hours)"
    ]

    phase2_data = df[phase2_columns].dropna()

    print("\n--- phase 2 stats ---")
    print(phase2_data.describe())

    return phase2_data

# phase 2 - exploratory data analysis
def phase2_eda(df):
    """
    visualize the relationship between each Phase 2 predictor
    and retail price.
    """

    # ram vs retail price
    plt.scatter(df["RAM (GB)"], df["Retail Price"])
    plt.xlabel("RAM (GB)")
    plt.ylabel("Retail Price ($)")
    plt.title("Retail Price vs. RAM")
    plt.show()

    # battery life vs retail price
    plt.scatter(df["Battery Life (Hours)"], df["Retail Price"])
    plt.xlabel("Battery Life (Hours)")
    plt.ylabel("Retail Price ($)")
    plt.title("Retail Price vs. Battery Life")
    plt.show()

    # fyi:
    # hd Size       -> positive relationship with price
    # ram           -> higher RAM generally associated with higher price
    # battery life  -> longer battery life generally associated with higher price

# phase 2 - multicollinearity check
def check_multicollinearity(df):
    """
    check correlations among the independent variables used in Model 2.
    """

    predictors = df[
        ["HD Size (GB)", "RAM (GB)", "Battery Life (Hours)"]
    ]

    print("\n--- phase 2 predictor correlations ---")
    print(predictors.corr())

    # multicollinearity observation:
    # the correlations among HD Size, RAM, and Battery Life are all weak
    # none of the pairwise correlations are close to common concern levels
    # such as 0.70 or higher which suggests that serious multicollinearity
    # is unlikely among these predictors.

# phase 2 - modeling
def build_phase2_model(df):
    """
    build a multiple linear regression model using HD Size, RAM,
    and Battery Life to predict Retail Price.
    """

    X = df[
        ["HD Size (GB)", "RAM (GB)", "Battery Life (Hours)"]
    ]

    y = df["Retail Price"]

    X = sm.add_constant(X)

    model2 = sm.OLS(y, X).fit()

    return model2

    """
    PHASE 2 SUMMARY

    The multivariate model includes HD Size, RAM, and Battery Life
    as predictors of Retail Price.

    Model Performance:
    R^2 = 0.711
    Adjusted R^2 = 0.711

    This means that the model explains approximately 71.1% of the
    variation in retail price, which is a substantial improvement
    over Model 1, which explained only 23.6%.

    Because Adjusted R^2 is nearly identical to R^2, the additional
    predictors appear to provide meaningful explanatory value rather
    than simply increasing model complexity.

    Coefficient Interpretation:

    HD Size coefficient = 0.3672
    Holding RAM and battery life constant, each additional 1 GB of
    storage is associated with approximately a $0.37 increase in
    predicted retail price.

    RAM coefficient = 46.2889
    Holding storage and battery life constant, each additional 1 GB
    of RAM is associated with approximately a $46.29 increase in
    predicted retail price.

    Battery Life coefficient = 47.0215
    Holding storage and RAM constant, each additional hour of battery
    life is associated with approximately a $47.02 increase in
    predicted retail price.

    P-Values:
    All predictors have p-values below 0.001, indicating that HD Size,
    RAM, and Battery Life are all statistically significant predictors
    of retail price in this model.

    Multicollinearity:
    Pairwise correlations among the independent variables were weak,
    so there is no obvious evidence of serious multicollinearity.

    Business Conclusion:
    Adding RAM and Battery Life significantly improves the model.
    The multivariate model explains much more of the variation in
    retail price than storage alone, making it a substantially stronger
    pricing model.

    The coefficient signs are intuitive: greater storage, more RAM,
    and longer battery life are all associated with higher retail price.
    """

# phase 3 - predictive task 1 - prediction using only hard drive size
def predict_model1(model):
    """
    Use Model 1 to predict the retail price of a laptop
    with 2000 GB of storage.
    """

    new_laptop = pd.DataFrame({
        "const": [1],
        "HD Size (GB)": [2000]
    })

    prediction = model.predict(new_laptop)

    predicted_price = prediction.iloc[0]

    print("\n--- phase 3: model 1 prediction ---")
    print(f"Predicted price for 2000 GB storage: ${predicted_price:.2f}")

    return predicted_price

# phase 3 - predictive task 2 - prediction using HD Size, RAM, and Battery Life
def predict_model2(model):
    """
    Use Model 2 to predict the retail price of a laptop with:
    - 2000 GB storage
    - 44 GB RAM
    - 4 hours battery life
    """

    new_laptop = pd.DataFrame({
        "const": [1],
        "HD Size (GB)": [2000],
        "RAM (GB)": [44],
        "Battery Life (Hours)": [4]
    })

    prediction = model.predict(new_laptop)

    predicted_price = prediction.iloc[0]

    print("\n--- phase 3: model 2 prediction ---")
    print(
        f"Predicted price for 2000 GB storage, "
        f"44 GB RAM, and 4 hours battery life: "
        f"${predicted_price:.2f}"
    )

    return predicted_price


# phase 3 - model comparison
def compare_predictions(model1_prediction, model2_prediction):
    """
    Compare the forecasts produced by Model 1 and Model 2.
    """

    difference = model2_prediction - model1_prediction

    print("\n--- phase 3: prediction comparison ---")
    print(f"Model 1 prediction: ${model1_prediction:.2f}")
    print(f"Model 2 prediction: ${model2_prediction:.2f}")
    print(f"Difference: ${difference:.2f}")

    """
    Model 2 should generally provide a more informed prediction
    because it incorporates multiple laptop specifications instead
    of relying only on storage capacity.

    Model 1 explained only about 23.6% of retail price variation,
    while Model 2 explained approximately 71.1%.

    However, both predictions require caution because the requested
    laptop configuration contains values far outside the ranges
    represented in the original dataset.

    In particular:
    - Training HD Size is approximately 40-300 GB
    - The requested HD Size is 2000 GB
    - Training RAM is approximately 1-2 GB
    - The requested RAM is 44 GB

    Therefore, these predictions involve extrapolation.
    """


# phase 3 - optimization
def optimize_model(df):
    """
    compare several regression models using test-set mean squared
    error (mse) and select the model with the lowest prediction error.
    """

    feature_sets = {
        "hd only": [
            "HD Size (GB)"
        ],

        "phase 2 model": [
            "HD Size (GB)",
            "RAM (GB)",
            "Battery Life (Hours)"
        ],

        "expanded hardware model": [
            "HD Size (GB)",
            "RAM (GB)",
            "Battery Life (Hours)",
            "Processor Speeds (GHz)"
        ]
    }

    y = df["Retail Price"]

    results = []

    best_model = None
    best_features = None
    best_mse = float("inf")

    for model_name, features in feature_sets.items():

        # Keep only the required columns and remove missing rows
        model_data = df[features + ["Retail Price"]].dropna()

        X = model_data[features]
        y = model_data["Retail Price"]

        # Split the data so that the model is evaluated on observations
        # it was not trained on.
        X_train, X_test, y_train, y_test = train_test_split(
            X,
            y,
            test_size=0.20,
            random_state=42
        )

        # Add intercept
        X_train = sm.add_constant(X_train, has_constant="add")
        X_test = sm.add_constant(X_test, has_constant="add")

        # Train model
        model = sm.OLS(y_train, X_train).fit()

        # Predict test-set prices
        predictions = model.predict(X_test)

        # Calculate Mean Squared Error
        mse = mean_squared_error(y_test, predictions)

        results.append({
            "Model": model_name,
            "Features": features,
            "MSE": mse,
            "Adjusted R-Squared": model.rsquared_adj
        })

        # Track the model with the lowest MSE
        if mse < best_mse:
            best_mse = mse
            best_model = model
            best_features = features

    print("\n--- phase 3: model optimization results ---")

    for result in results:
        print(f"\nModel: {result['Model']}")
        print(f"Features: {result['Features']}")
        print(f"MSE: {result['MSE']:.2f}")
        print(
            f"Adjusted R-squared: "
            f"{result['Adjusted R-Squared']:.4f}"
        )

    print("\n--- optimal model ---")
    print(f"Selected Features: {best_features}")
    print(f"Lowest Test MSE: {best_mse:.2f}")

    return best_model, best_features, results

    """
    PHASE 3 OPTIMIZATION SUMMARY

    Three models were compared using an 80/20 train-test split.

    1. HD Only Model
    Adjusted R^2 = 0.2385
    Test MSE = 2927.65

    2. Phase 2 Model
    Predictors:
    - HD Size
    - RAM
    - Battery Life

    Adjusted R^2 = 0.7113
    Test MSE = 1095.33

    3. Expanded Hardware Model
    Predictors:
    - HD Size
    - RAM
    - Battery Life
    - Processor Speed

    Adjusted R^2 = 0.7459
    Test MSE = 941.25

    The expanded hardware model produced the lowest test MSE and the
    highest Adjusted R-squared of the candidate models.

    This suggests that Processor Speed contributes additional predictive
    information beyond HD Size, RAM, and Battery Life.

    Because the model was evaluated on a separate test set rather than
    the same observations used for training, the MSE provides a better
    measure of predictive performance on unseen data.

    Among the tested models, the expanded hardware model is therefore
    the preferred model for predicting retail price.
    """

# main
def main():

    # data ingestion
    df = load_data("LaptopSalesJanuary2008.csv")

    # data processing
    phase1_data = preprocess_data(df)

    # phase 1 eda
    phase1_eda(phase1_data)

    # phase 1 modeling
    model1 = build_phase1_model(phase1_data)

    # phase 1 eval
    evaluate_phase1_model(model1)

    # phase 2 data preparation
    phase2_data = prepare_phase2_data(df)

    # phase 2 eda
    phase2_eda(phase2_data)

    # phase 2 multicollinearity check
    check_multicollinearity(phase2_data)

    # phase 2 modeling
    model2 = build_phase2_model(phase2_data)

    print(model2.summary())

    # phase 3 - predictive task 1
    model1_prediction = predict_model1(model1)

    # phase 3 - predictive task 2
    model2_prediction = predict_model2(model2)

    # phase 3 - compare predictions
    compare_predictions(model1_prediction, model2_prediction)

    # phase 3 - optimization
    optimal_model, optimal_features, optimization_results = optimize_model(df)

# main for run
if __name__ == "__main__":
    main()

"""
PHASE 3 FORECAST COMPARISON

Model 1 predicted price:
$1027.45

Model 2 predicted price:
$3078.57

Difference:
$2051.12

The large difference occurs because Model 2 incorporates additional
hardware specifications, especially RAM.

The RAM coefficient in Model 2 is approximately $46.29 per GB.
Using 44 GB of RAM therefore contributes more than $2,000 to the
predicted price.

Model 2 is generally the stronger predictive model because it explains
approximately 71.1% of retail price variation compared with 23.6%
for Model 1.

However, caution is required when interpreting these specific forecasts.

The historical dataset contains approximately:
- 40 to 300 GB of storage
- 1 to 2 GB of RAM
- 4 to 6 hours of battery life

The requested configuration contains:
- 2000 GB storage
- 44 GB RAM
- 4 hours battery life

Therefore, the predictions for storage and RAM involve substantial
extrapolation beyond the range of the training data.

Conclusion:
Model 2 is more informative and performs substantially better within
the observed dataset, but confidence in the specific $3078.57 forecast
is limited because the requested hardware configuration is far outside
the historical data used to estimate the model.
"""