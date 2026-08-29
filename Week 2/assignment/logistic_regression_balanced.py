"""Logistic regression on LendingClub data with balanced class weights.

Uses class_weight="balanced" plus feature scaling so the model distinguishes
the minority class instead of predicting the majority class almost exclusively.
"""

import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import confusion_matrix, accuracy_score

TARGET = "loan_status"
FEATURES = ["home_ownership", "income", "dti", "fico"]

TRAIN_FILE = "lendingclub_traindata.xlsx"
TEST_FILE = "lendingclub_testdata.xlsx"
VAL_FILE = "lendingclub_valdata.xlsx"


def load(path):
    """Load a dataset and standardize the misspelled home_ownership column."""
    df = pd.read_excel(path)
    df = df.rename(columns={"homw_ownership": "home_ownership"})
    return df[FEATURES], df[TARGET]


def evaluate(model, scaler, X, y, name):
    """Print the confusion matrix and accuracy for a scaled dataset."""
    pred = model.predict(scaler.transform(X))
    print(f"\n{name}")
    print("Confusion matrix:")
    print(confusion_matrix(y, pred))
    print(f"Accuracy: {accuracy_score(y, pred):.4f}")


# Scale features and train with balanced class weights
X_train, y_train = load(TRAIN_FILE)
scaler = StandardScaler().fit(X_train)
model = LogisticRegression(max_iter=1000, class_weight="balanced")
model.fit(scaler.transform(X_train), y_train)

# Evaluate on all three datasets (scaler fit on train, applied everywhere)
evaluate(model, scaler, X_train, y_train, "Training data")
evaluate(model, scaler, *load(TEST_FILE), "Test data")
evaluate(model, scaler, *load(VAL_FILE), "Validation data")
