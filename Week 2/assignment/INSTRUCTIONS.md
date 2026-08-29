# LendingClub Loan Model: Problem Statement and Data Dictionary

## 1. The Problem in Plain English

We want to predict whether a LendingClub loan will turn out good or bad, using a few simple facts we know about the borrower at the time of the loan.

For each loan, we know four things about the borrower: whether they own their home, their income, their debt-to-income ratio, and their FICO credit score. We also know the final outcome of the loan, recorded as `loan_status`. Our goal is to build a model that looks at the four borrower facts and predicts the outcome.

The outcome has two possible values (`0` and `1`), so this is a **binary classification** problem, and we solve it with **logistic regression**. In the data, about 79% of loans are class `1` and about 21% are class `0`, so the two outcomes are imbalanced—most loans fall into one group. This matters because a model can score high accuracy simply by always guessing the common outcome, without really learning to tell the two apart.

To judge the model honestly, we split the data into three separate sets and use a confusion matrix (a table of correct and incorrect predictions) on each:

| Dataset | Rows | Purpose |
|---|---:|---|
| Training | 7,000 | The data the model learns from. |
| Test | 2,290 | Held-back data used to check the model on rows it did not learn from. |
| Validation | 3,000 | A second held-back set used as a final independent check. |

**In short:** Learn the pattern on the training set, then confirm the pattern holds on the test and validation sets.

## 2. Data Dictionary

Every dataset has the same five columns. The first four are inputs (features); the last one is the outcome we predict (the target). All values are numeric, so no text cleaning is needed.

### Input Features

| Column | Type | Range in Data | Plain-English Meaning |
|---|---|---:|---|
| `home_ownership` | Whole number (`0` or `1`) | `0` or `1` | Whether the borrower owns their home. Coded as two categories: `0` and `1`. |
| `income` | Decimal number | 0 to 1,500,000 | The borrower's annual income, in dollars. |
| `dti` | Decimal number | 0 to 244.6 | Debt-to-income ratio: the borrower's monthly debt payments as a percentage of monthly income. Higher means more of their income is already committed to debt. |
| `fico` | Whole number | 660 to 845 | The borrower's FICO credit score. Higher means better credit history. |

### Target (What We Predict)

| Column | Type | Values | Plain-English Meaning |
|---|---|---|---|
| `loan_status` | Whole number (`0` or `1`) | `0` or `1` | The final outcome of the loan. `1` is the common outcome (about 79% of loans), and `0` is the rarer outcome (about 21%). Class `1` represents the “good” outcome (loan repaid), and class `0` represents the “bad” outcome (loan defaulted). |

> **Note on encoding:** `home_ownership` and `loan_status` arrive already converted to numbers (`0` and `1`) rather than text labels. The exact label behind each code is not stored in the files; the meanings above reflect the standard LendingClub convention and the fact that the repaid (“good”) outcome is the majority.
