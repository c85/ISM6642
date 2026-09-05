# Customer Segmentation with K-Means Clustering

**Course:** MSIS — Business Analytics  
**Points:** 100  
**Assignment group:** Problem Sets  
**Due:** September 11, 2025, 11:59 PM (America/New_York)  
**Submission type:** File upload  
**Allowed file types:** `.py`, `.ipynb`, `.pdf`, `.md`

## Business Context

You are the newly hired analytics lead at **Sunset Palms Mall**, a regional shopping center with 180 tenant stores and a loyalty program of 200 enrolled members. For each member, the mall has collected:

- **Age** and **gender** from enrollment
- **Annual income (k$)**, self-reported at enrollment
- **Spending score (1–100)**, an internal index computed from purchase frequency, basket size, and category breadth

The marketing director has a problem. The mall currently sends the same promotional email and coupon book to every member, and the results are poor:

- The redemption rate is only about 2%.
- Tenant stores complain that coupons are redeemed by customers who would have purchased anyway, eroding margins without generating new traffic.
- The quarterly promotion budget is fixed at $50,000, so every wasted coupon is money not spent on a customer who might actually respond.

At Monday’s meeting, the director asks:

> Can you divide our loyalty members into a handful of distinct customer segments—based on how much they earn and how they actually spend—so that each segment gets a promotion designed for it? And tell me: how many segments should we have? Every additional segment means another campaign my team has to design, fund, and measure.

Your job is to answer both questions using k-means clustering, then translate your statistical results into recommendations the marketing director can act on.

## The Data

Download `Mall_Customers.csv` from Kaggle. It contains these columns:

- `CustomerID`
- `Gender`
- `Age`
- `Annual Income (k$)`
- `Spending Score (1-100)`

Use these two features for clustering:

- `Annual Income (k$)`
- `Spending Score (1-100)`

Extension Question 2 asks you to reflect on this feature choice.

## Starter Code

Save your work as `cluster_analysis.py`, or use a Jupyter notebook (`.ipynb`). Run the analysis for `k = 3`, `k = 4`, and `k = 6`.

```python
import pandas as pd
from sklearn.cluster import KMeans


data = pd.read_csv("Mall_Customers.csv")
features = ["Annual Income (k$)", "Spending Score (1-100)"]
X = data[features]

k = 3  # Change this to 4 and 6 for Parts 2 and 3.
model = KMeans(n_clusters=k, random_state=42)
data["Cluster"] = model.fit_predict(X)

summary = (
    data.groupby("Cluster")[features]
    .agg(["count", "mean", "std"])
    .round(2)
)

print(f"\n=== Summary for k = {k} ===")
print(summary)
```

The summary for each run must show the cluster size, mean, and standard deviation for annual income and spending score.

## Tasks

### Part 1 — Setup and Baseline Segmentation (`k = 3`)

1. Ensure Python 3.x is installed with `pandas` and `scikit-learn`.
2. Run the starter code with `k = 3` and verify that it prints the count, mean, and standard deviation of income and spending score for each cluster.
3. For each of the three clusters, write a one-line customer persona. For example: *“Mid-income, moderate spenders—the mall’s mainstream shopper.”*

### Part 2 — Experimentation (`k = 4` and `k = 6`)

1. Rerun the analysis with `k = 4`, then with `k = 6`.
2. Capture the summary table for each run.
3. As you move from 3 → 4 → 6 segments, assess the following:
   - **Homogeneity:** Do standard deviations within clusters shrink? In business terms, is each segment becoming a group of genuinely similar customers?
   - **Size balance:** Do some clusters become very small? In business terms, is any segment too small to justify its own campaign?

### Part 3 — Report to the Marketing Director

Assemble one report—PDF, Markdown, or a section embedded in your notebook—with three sections:

1. **`k = 3`:** Summary table and a brief observation (2–3 sentences).
2. **`k = 4`:** Summary table and a brief observation.
3. **`k = 6`:** Summary table and a brief observation.

Each observation must address both homogeneity and size balance. Connect the statistics to the business. For example, explain what a large within-cluster standard deviation in spending score means for a marketer sending one offer to that entire cluster.

### Part 4 — Recommendation and Promotion Plan

End your report with a short recommendation section (½–1 page) that answers the director’s questions:

1. **Which value of `k` do you recommend, and why?** Justify the decision using both statistical evidence (homogeneity and size balance) and business logic (campaign design costs and minimum viable segment size).
2. **For your recommended `k`, propose one promotion per segment.** For each cluster, state:
   - The persona, including income/spending profile and cluster size
   - The offer (for example, a VIP preview event, points multiplier, or clearance email)
   - The rationale, including any segment that should **not** receive a discount and why that protects margin

**Hint:** Watch for two clusters with similar incomes but very different spending scores. A campaign that targets income alone would treat them identically. Should it?

## Deliverables

| File | Required contents |
| --- | --- |
| `cluster_analysis.py` or `.ipynb` | Working code for all three runs. It must run without errors. |
| `cluster_report.pdf` or `.md` | Three summary tables and observations (Part 3), plus the recommendation and promotion plan (Part 4). A separate report is not required if all content is included in the notebook. |

Submit via Canvas by the deadline.

## Grading Criteria

| Component | Weight |
| --- | ---: |
| Script correctness and reproducibility (runs without error; `random_state=42`) | 25% |
| Accuracy of summary tables (`k = 3`, `k = 4`, and `k = 6`) | 20% |
| Quality of observations: homogeneity and size balance tied to business meaning | 25% |
| Recommendation and promotion plan: sound choice of `k`, persona-appropriate offers, and margin logic | 20% |
| Report formatting and clarity | 10% |

## Challenge Questions (up to 5 Bonus Points)

1. **Budget allocation:** For your recommended `k`, propose how to split the $50,000 quarterly budget across segments. Justify your allocation using cluster size and expected uplift.
2. **Feature choice:** The model clusters only on income and spending score. What would change if age were added? What business or ethical risk arises from clustering on gender for promotional targeting?
3. **Measurement:** The director asks, “How will we know the segmented campaigns actually worked?” Describe a simple holdout/control-group design to measure incremental lift per segment.

## Academic Integrity and AI Tool Use

Follow the course policy on AI tool use stated in the syllabus. You must be able to explain every line of submitted code and every claim in your report. Do not upload the dataset or any student data to external services beyond what the assignment requires.
