from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt
import statsmodels.api as sm

# Load the dataset from the same folder as this script
file_path = Path(__file__).resolve().parent / "LaptopSalesJanuary2008.csv"
df = pd.read_csv(file_path)

# Print the first few rows to understand the structure
print("\nPreview of dataset:")
print(df.head())

# Detect and print data types for each column
print("\nData types of each column:")
print(df.dtypes)

# Identify which columns are numeric
print("\nIdentifying numeric columns:")
numeric_cols = df.select_dtypes(include='number').columns
print("Numeric columns:", list(numeric_cols))

# Calculate mean and standard deviation for numeric columns
print("\nMean of each numeric variable:")
print(df[numeric_cols].mean())

print("\nStandard deviation of each numeric variable:")
print(df[numeric_cols].std())

# Plot box-and-whisker plots for each numeric variable
print("\nDisplaying box-and-whisker plots for numeric variables...")
df[numeric_cols].plot(kind='box', subplots=True, layout=(len(numeric_cols), 1), figsize=(8, 5 * len(numeric_cols)), sharex=False)
plt.tight_layout()
plt.show()

# Linear regression with Price as dependent variable and RAM, HDSize as independent variables
print("\nPerforming linear regression with Price as dependent variable and RAM, HDSize as independent variables...")
X = df[["RAM (GB)", "HD Size (GB)"]]
y = df["Retail Price"]

# Add constant to predictor variables
X = sm.add_constant(X)

# Fit the regression model
model = sm.OLS(y, X).fit()

# Print out the regression results
print(model.summary())

# Predict the price of a computer with 4 GB RAM and 10 GB HDSize
print("\nPredicting price for computer with 4 GB RAM and 10 GB HDSize...")
new_data = pd.DataFrame({"const": [1], "RAM (GB)": [4], "HDSize": [10]})
predicted_price = model.predict(new_data)
print(f"Predicted Price: ${predicted_price.iloc[0]:.2f}")

# Create a matplotlib fit plot for Y and predicted Y
print("\nCreating fit plot...")
predicted_y = model.predict(X)
plt.figure(figsize=(10, 6))
plt.scatter(y, predicted_y, alpha=0.6, edgecolor='k')
plt.plot([y.min(), y.max()], [y.min(), y.max()], 'r--', lw=2)
plt.xlabel('Actual Price')
plt.ylabel('Predicted Price')
plt.title('Actual vs Predicted Retail Price')
plt.grid(True)
plt.tight_layout()
plt.show()

# Residual plot
print("\nCreating residual plot...")
residuals = y - predicted_y
plt.figure(figsize=(10, 6))
plt.scatter(predicted_y, residuals, alpha=0.6, edgecolor='k')
plt.axhline(0, color='red', linestyle='--', linewidth=2)
plt.xlabel('Predicted Price')
plt.ylabel('Residuals')
plt.title('Residual Plot')
plt.grid(True)
plt.tight_layout()
plt.show()

