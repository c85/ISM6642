"""
instructor_solution_retail.py
-----------------------------
Reference solution for the SunCoast Retail Mart relabeling assignment.
Run:  python instructor_solution_retail.py
"""

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
from sklearn.model_selection import train_test_split
from sklearn.metrics import confusion_matrix, accuracy_score, roc_auc_score

df = pd.read_csv("retail_relabel.csv")

# ---------- Part 1: Feature engineering ----------
df["CompAvg"] = df[["Competitor_BigBoxDepot", "Competitor_ValueMart",
                    "Competitor_QuickShop"]].mean(axis=1)
df["GapPct"] = 100 * (df["StorePrice"] - df["CompAvg"]) / df["CompAvg"]
df["AbsGapPct"] = df["GapPct"].abs()
df["LogUnits"] = np.log(df["WeeklyUnitsSold"])
df["MarginPct"] = 100 * (df["StorePrice"] - df["UnitCost"]) / df["StorePrice"]

print(df["Relabel"].value_counts(normalize=True).rename("share"), "\n")
print(df.groupby("ElectronicShelfLabel")["Relabel"].mean().round(3), "\n")

# ---------- Part 2: Naive model (signed gap — a deliberate trap) ----------
m1 = smf.logit("Relabel ~ GapPct + UnitCost + RelabelCost", data=df).fit(disp=0)
print("MODEL 1 (signed gap)  pseudo-R2=%.3f  AIC=%.1f" % (m1.prsquared, m1.aic))

# ---------- Part 3: Correct model (absolute gap + full drivers) ----------
m2 = smf.logit(
    "Relabel ~ AbsGapPct + CostChangePct + LogUnits + RelabelCost "
    "+ DaysSinceLastChange + UnitCost", data=df).fit(disp=0)
print("MODEL 2 (abs gap)     pseudo-R2=%.3f  AIC=%.1f\n" % (m2.prsquared, m2.aic))
print(m2.summary2().tables[1].round(4), "\n")

or_table = pd.DataFrame({
    "OddsRatio": np.exp(m2.params),
    "CI_low": np.exp(m2.conf_int()[0]),
    "CI_high": np.exp(m2.conf_int()[1]),
}).round(3)
print("Odds ratios:\n", or_table, "\n")

# ---------- Part 4: Out-of-sample evaluation ----------
feats = ["AbsGapPct", "CostChangePct", "LogUnits", "RelabelCost",
         "DaysSinceLastChange", "UnitCost"]
X_tr, X_te, y_tr, y_te = train_test_split(
    df[feats], df["Relabel"], test_size=0.30, random_state=7,
    stratify=df["Relabel"])
train = X_tr.copy(); train["Relabel"] = y_tr
m3 = smf.logit("Relabel ~ " + " + ".join(feats), data=train).fit(disp=0)
p_hat = m3.predict(X_te)
y_hat = (p_hat >= 0.5).astype(int)
print("Confusion matrix:\n", confusion_matrix(y_te, y_hat))
print("Accuracy: %.3f  AUC: %.3f\n" % (accuracy_score(y_te, y_hat),
                                       roc_auc_score(y_te, p_hat)))

# ---------- Part 5: Economic threshold ----------
# Expected weekly value of relabeling one unit of |gap| on a fast mover vs the
# relabel cost: students compute break-even p* = C / (C + B) style reasoning.
test = X_te.copy()
test["p_hat"] = p_hat
test["ExpectedWeeklyLoss"] = (test["AbsGapPct"] / 100) \
    * df.loc[test.index, "StorePrice"] * df.loc[test.index, "WeeklyUnitsSold"]
test["NetBenefit"] = test["ExpectedWeeklyLoss"] - test["RelabelCost"]
print("Share of SKUs where one week of mispricing already exceeds the "
      "relabel cost: %.3f" % (test["NetBenefit"] > 0).mean())

# ---------- Marginal effects ----------
print("\nAverage marginal effects:\n", m2.get_margeff().summary())
