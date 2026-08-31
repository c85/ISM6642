# Florida Fitness Market Analysis

This folder contains the completed Week 1 and Week 2 assignment workflow for the LA Fitness expansion case.

## Submission files

- `Florida_Fitness_Market_EDA_Report.docx`: summary statistics, correlations, required charts, outliers, and EDA conclusions.
- `Florida_Fitness_Market_Predictions_and_Insights.docx`: full and refined OLS models, diagnostics, scenario predictions, and the ranked expansion shortlist.
- `data/MainDataset.csv`: one row for each of Florida's 67 counties and the eight required columns.
- `data/gym_locations.csv`: 387 accepted Google Places records, exact-county filtered and deduplicated by Place ID, with each gym's name and formatted street address.
- `data/demographic_data.csv`: 2020 Census population, 2021 ACS income, Gazetteer land area, and calculated density.
- `data/membership_prices.csv`: transparently estimated county membership-price target.
- `outputs/`: statistical tables, model summaries, diagnostics, scenarios, rankings, query audit, and figures.

## Reproduce the analysis

Use Python 3.11 or later, install `requirements.txt`, and place valid keys in:

- `census_api_key.txt`
- `google_places_api_key.txt`

Run from this directory:

```bash
python fitness_market_analysis.py
```

The submitted location file already includes each gym's name and formatted street address. Running this command makes live Google Places API requests across 67 counties and five brands.

## Important limitation

Demographic and fitness-location data are observed from the cited APIs. County-level membership prices were not available as a consistent public dataset, so `MembershipPrice` is simulated with a disclosed, reproducible formula, as permitted by the assignment. Accordingly, the regression and county ranking demonstrate the required analytical workflow and should not be treated as independent evidence for a capital decision.

API keys are read locally and excluded from analytical outputs and version control.
