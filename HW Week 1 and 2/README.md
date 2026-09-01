# Florida Fitness Market Analysis

This folder contains the completed Week 1 and Week 2 assignment workflow for the LA Fitness expansion case.

## Submission files

- `reports/Florida_Fitness_Market_EDA_Report.docx`: summary statistics, correlations, required charts, outliers, and EDA conclusions.
- `reports/Florida_Fitness_Market_Predictions_and_Insights.docx`: full and refined OLS models, diagnostics, scenario predictions, and the ranked expansion shortlist.
- `data/MainDataset.csv`: one row for each of Florida's 67 counties and the eight required columns.
- `data/gym_locations.csv`: 428 accepted Google Places records for LA Fitness and the four tracked competitors (Planet Fitness, YouFit, Gold's Gym, and Orangetheory Fitness), exact-county filtered and deduplicated by Place ID, with each gym's name and formatted street address.
- `data/demographic_data.csv`: 2020 Census population, 2021 ACS income, Gazetteer land area, and calculated density.
- `data/la_fitness_pricing.csv`: official LA Fitness club-level rate observations collected through the public membership-signup flow.
- `data/gym_membership_pricing.csv`: long-form official plan-price observations for all five tracked chains, including dues frequency, initiation fees, annual fees, promotions, source URLs, and retrieval timestamps.
- `data/pricing_collection_audit.csv`: per-chain coverage and non-observed source records.
- `data/membership_prices.csv`: county membership-price target; local advertised-offer averages are retained where available and statewide-median estimates are explicitly labeled elsewhere.
- `scripts/`: the live collectors, analysis workflow, and report updater.
- `outputs/`: statistical tables, model summaries, diagnostics, scenarios, rankings, query audit, and figures.

## Reproduce the analysis

Use Python 3.11 or later, install `requirements.txt`, and place valid keys in:

- `census_api_key.txt`
- `google_places_api_key.txt`

Run from this directory:

```bash
python scripts/fitness_market_analysis.py
```

The submitted location file already includes each gym's name and formatted street address. Running this command makes live Google Places API requests across 67 counties and five brands. The tracked competitor set replaces 24 Hour Fitness with YouFit, whose official Florida directory is used as a footprint cross-check.

To refresh the official pricing observations before rebuilding the analysis:

```bash
python scripts/collect_la_fitness_pricing.py --delay 0.6
python scripts/collect_membership_pricing.py --delay 0.08
python scripts/fitness_market_analysis.py
python scripts/update_reports.py
```

The pricing collector uses public official enrollment or studio pages/API responses. It records a missing or inaccessible rate instead of inventing a value.

## Important limitation

Demographic, fitness-location, and raw plan-price data are observed from the cited APIs or official public enrollment pages. Advertised prices are not transaction prices and vary by plan, franchise, studio, promotion, and retrieval date. In the current run, 32 counties have local official price observations; the other 35 use a transparent statewide median only because no local public rate was available. Planet Fitness contributes real chainwide published starting rates, but its official site says local prices vary, so those rates are retained as a baseline and are not assigned to counties. The regression and county ranking should not be treated as independent evidence for a capital decision without broader comparable local price coverage.

API keys are read locally and excluded from analytical outputs and version control.
