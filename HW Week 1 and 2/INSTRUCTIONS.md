# MSIS Data Science Assignment

## Fitness Market Analysis: LA Fitness Expansion Strategy

## Assignment Overview

In this assignment, you will develop a predictive model to support LA Fitness expansion decisions in Florida. You will combine geospatial data from Google Maps (gym locations), demographic data (county populations), and market data to build a linear regression model that predicts gym membership pricing and evaluates market potential.

This realistic business analytics scenario integrates data collection, data wrangling, exploratory data analysis, and statistical modeling. You may replicate the workflow and data pipeline described below or improve upon it.

Complete the assignment individually or in a group of three or five. In a group, team members may divide the data-collection tasks. If you need help and are unable to resolve an issue, schedule time with the instructor before July 9, 2026.

If required data is difficult or impossible to obtain, you may create dummy or simulated data and associated variables. Clearly identify any simulated data and explain why actual data was unavailable.

You may use any AI tool available to you. Claude Code may be especially useful for this type of work.

## Submission Requirements

Submit the following:

- All code used for data collection, processing, analysis, modeling, and prediction
- The Word document described in Step 5
- The supporting CSV files and analytical outputs specified below

## Learning Objectives

By completing this assignment, you will learn to:

- Retrieve geospatial data from external APIs, such as the Google Maps Places API
- Integrate fitness-center, demographic, and market data from multiple sources
- Perform exploratory data analysis (EDA) using appropriate visualizations
- Develop and validate a linear regression model
- Generate business predictions and communicate actionable findings

## Dataset Scope

- **Geographic focus:** All 67 Florida counties
- **Primary data source:** Google Maps Places API or a CSV export created through manual searches
- **Secondary data sources:** U.S. Census Bureau data and Zillow or other relevant economic indicators
- **Competitors to track:** Planet Fitness, 24 Hour Fitness, Gold's Gym, and Orangetheory Fitness

## Key Variables

### Dependent Variable (Target)

| Variable | Definition | Data Source or Derivation |
| --- | --- | --- |
| `MembershipPrice` | Average monthly gym membership price, in U.S. dollars, for each county market | Gym websites, Google searches, and manual web research |

### Independent Variables

| Variable | Definition | Data Source or Derivation |
| --- | --- | --- |
| `CountyPopulation` | Total county population | U.S. Census Bureau (2020 Census) |
| `LAFitnessLocations` | Number of LA Fitness locations per county | Google Maps Places API or manual search/export |
| `CompetitorLocations` | Number of competing fitness-chain locations per county | Google Maps Places API or manual search aggregation |
| `MedianHouseholdIncome` | Median household income in U.S. dollars; a proxy for purchasing power | U.S. Census Bureau American Community Survey (ACS) |
| `PopulationDensity` | Number of residents per square mile | `CountyPopulation / LandAreaSqMiles` |
| `AvgGymRating` | Average Google Maps rating for all fitness centers in the county, on a 1–5 scale | Google Maps Places API ratings field |

## Multi-Step Assignment Workflow

### Step 1: Data Collection (Week 1)

#### 1.1 Google Maps Fitness-Location Extraction

1. Use the Google Maps Places API, or a manual search/export process, to retrieve all LA Fitness locations in Florida.
2. Collect each location's name, latitude, longitude, address, county, Google rating, and review count.
3. Repeat the process for Planet Fitness, 24 Hour Fitness, Gold's Gym, and Orangetheory Fitness.

**Output:** A CSV file containing the following columns:

```text
LocationID, GymChain, CountyName, Latitude, Longitude, Rating, ReviewCount
```

#### 1.2 Census and Demographic Data

1. Download 2020 U.S. Census population data for all 67 Florida counties.
2. Download 2021 ACS median-household-income data.
3. Obtain county land area and calculate population density.

**Output:** A CSV file containing the following columns:

```text
CountyName, CountyPopulation, MedianHouseholdIncome, LandAreaSqMiles, PopulationDensity
```

#### 1.3 Membership Price Research

1. Research and document the average monthly gym membership price for each county.
2. Use credible sources such as gym websites, review platforms, and news articles about regional fitness pricing.
3. If direct data is unavailable for a smaller county, estimate its price using comparable nearby counties. Document and justify the estimation method.

**Output:** A CSV file containing the following columns:

```text
CountyName, MembershipPrice
```

### Step 2: Data Integration and Aggregation (Week 2)

1. Standardize county names and merge all data sources using `CountyName`.
2. Aggregate gym-location data by county to calculate `LAFitnessLocations`, `CompetitorLocations`, and `AvgGymRating`.
3. Address missing values using an appropriate method, such as imputation, listwise deletion, or sensitivity analysis. Explain and justify your choice.
4. Create a final dataset with one row per Florida county and all variables listed above.

**Output:** `MainDataset.csv` with 67 rows and 8 columns: `CountyName`, the dependent variable, and the six independent variables.

### Step 3: Exploratory Data Analysis (Week 2)

1. Calculate the mean, median, standard deviation, minimum, and maximum for all numeric variables.
2. Create a correlation matrix showing the relationships among all numeric variables, including `MembershipPrice`.
3. Create at least five visualizations, including:
   - A scatter plot of `CountyPopulation` versus `MembershipPrice`
   - A scatter plot of `MedianHouseholdIncome` versus `MembershipPrice`
   - A scatter plot of `LAFitnessLocations` versus `MembershipPrice`
   - A histogram showing the distribution of `MembershipPrice`
   - A heatmap of the correlation matrix
4. Identify outliers and discuss their possible business significance.

**Output:** An EDA report in Word or PDF format containing summary statistics, tables, findings, and at least five visualizations.

### Step 4: Model Development (Week 2)

#### Build the Model

Estimate an Ordinary Least Squares (OLS) linear regression model using:

- **Dependent variable:** `MembershipPrice`
- **Independent variables:** `CountyPopulation`, `LAFitnessLocations`, `CompetitorLocations`, `MedianHouseholdIncome`, `PopulationDensity`, and `AvgGymRating`

#### Evaluate Model Diagnostics

- Report R-squared and adjusted R-squared.
- Report coefficients, p-values, and 95% confidence intervals.
- Check for multicollinearity using variance inflation factors (VIF); values above 5 should be flagged as potential concerns.
- Create an actual-versus-predicted plot, a Q-Q plot, and a residuals-versus-fitted plot.
- Test residual normality using the Shapiro-Wilk test.
- Test homoscedasticity using the Breusch-Pagan test.

#### Refine the Model

- Evaluate variables with p-values greater than 0.05 and, when justified, remove non-significant variables before re-estimating the model.
- Compare the full model with the refined, parsimonious model.
- Explain and justify all model changes.

**Output:** Regression results from Python `statsmodels` or R, saved as a table or image.

### Step 5: Predictions and Business Insights (Week 2)

1. Use the final model to predict `MembershipPrice` for three hypothetical scenarios:
   - **Scenario A:** A high-potential, low-competition county—for example, a rural county with a population of 50,000, two LA Fitness locations, and one competitor
   - **Scenario B:** An urban, high-competition county—for example, Miami-Dade County with a population of 2.6 million, 15 LA Fitness locations, and 30 competitors
   - **Scenario C:** A user-defined scenario representing a target expansion market
2. Specify values for every predictor used in the final model for each scenario.
3. Calculate and report 95% confidence intervals for the predictions.
4. Interpret the model:
   - Which factors most strongly influence membership pricing?
   - How does competition affect price?
5. Recommend and rank the top five Florida counties for LA Fitness expansion based on market potential. Clearly explain the criteria used for the ranking.

**Output:** A Predictions and Business Insights report in Word format containing the scenarios, predictions, interpretations, and recommendations.
