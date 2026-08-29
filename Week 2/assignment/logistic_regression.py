"""Logistic regression on LendingClub data: train, test, and validate."""

import pandas as pd
from sklearn.linear_model import LogisticRegression
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


def evaluate(model, X, y, name):
    """Print the confusion matrix and accuracy for a dataset."""
    pred = model.predict(X)
    print(f"\n{name}")
    print("Confusion matrix:")
    print(confusion_matrix(y, pred))
    print(f"Accuracy: {accuracy_score(y, pred):.4f}")


# Train the model
X_train, y_train = load(TRAIN_FILE)
model = LogisticRegression(max_iter=1000)
model.fit(X_train, y_train)

# Evaluate on all three datasets
evaluate(model, X_train, y_train, "Training data")
evaluate(model, *load(TEST_FILE), "Test data")
evaluate(model, *load(VAL_FILE), "Validation data")
