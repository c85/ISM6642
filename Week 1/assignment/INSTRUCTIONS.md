# Assignment 1: Laptop Price Prediction

## Objective

In this lab, you will act as a data analyst for a global consumer electronics retailer. Using the provided `LaptopSalesJanuary2008.csv` dataset, you will develop, evaluate, and deploy predictive models to inform pricing strategies and inventory planning.

## Submission Requirements

- **Codebase:** Submit a well-commented script (`FirstNameLastName-Assignment1.py`) or notebook (`FirstNameLastName-Assignment1.ipynb`) that follows modular programming principles. Include clear sections for data ingestion, preprocessing, modeling, and evaluation. If you use GitHub, check your code into a repository and share the repository URL instead of copying and pasting your code here.
- **Executive summary:** Submit a concise Word document containing key visualizations, model diagnostics, and business insights. Include screenshots of key runs from each phase.

## Phase 1: The Foundation (Simple Linear Regression)

**Goal:** Quantify the relationship between hardware specifications and market value.

**Task:** Model `Retail.Price` as a function of `HD.Size.GB`.

### The Analyst's Challenge

1. Formulate a business hypothesis regarding the impact of storage capacity on price.
2. Perform an exploratory data analysis (EDA) to visualize the linearity of this relationship.
3. Report the coefficient of determination ($R^2$) and the p-value. What do these values tell you about the strength of storage capacity as a predictor of price?

## Phase 2: Multivariate Optimization

**Goal:** Reduce residual error by accounting for multidimensional consumer preferences.

**Task:** Expand your model by integrating variables such as `RAM`, `BatteryLife`, and other relevant features.

### The Analyst's Challenge

1. Check for multicollinearity among your independent variables. How does adding these variables affect the adjusted $R^2$?
2. Interpret the coefficients of your new model. Are there any counterintuitive findings?

## Phase 3: The Challenge (Predictive Deployment)

**Goal:** Apply your models to generate actionable business intelligence.

**Scenario:** A regional manager asks for a price estimate for an upcoming model with specific configurations.

### Predictive Tasks

1. Using Model 1, forecast the price of a laptop with 2,000 GB of storage.
2. Using Model 2 (the multivariate approach), forecast the price of a laptop with 2,000 GB of storage, 44 GB of RAM, and four hours of battery life.

### Strategy

Compare the two forecasts. Which model provides greater confidence, and why?

### Optimization

Can you engineer a feature or select a subset of variables that minimizes mean squared error (MSE)? Use all available data to build the most optimal model possible.

## Tips for Success

- **Business context:** Always frame your results in terms of business impact. If a model is inaccurate, what are the implications for the company's margin or competitive positioning?
- **Validation:** Do not just report the numbers—explain what they mean for the business.
- **Consistency:** Use clean, professional formatting in your reports, just as you would for a stakeholder presentation.

## Attachment

- [`LaptopSalesJanuary2008.csv`](LaptopSalesJanuary2008.csv)
