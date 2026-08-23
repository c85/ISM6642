"""Descriptive statistics review for quarterly sales revenue."""

import numpy as np
import matplotlib.pyplot as plt
from collections import Counter
import statistics

# Sales revenue per quarter (in thousands of dollars)
data = [45, 52, 48, 61, 55, 49, 58, 63, 51, 47, 59, 64]


def calculate_mean(values):
    """Return the arithmetic mean of values."""
    return sum(values) / len(values)


def calculate_median(values):
    """Return the median of values."""
    return statistics.median(values)


def calculate_mode(values):
    """Return a list of modes, or an empty list when every value is unique."""
    counts = Counter(values)
    highest_frequency = max(counts.values())

    if highest_frequency == 1:
        return []

    return [value for value, count in counts.items() if count == highest_frequency]


def calculate_range(values):
    """Return the difference between the largest and smallest values."""
    return max(values) - min(values)


def calculate_sample_std_dev(values):
    """Return the sample standard deviation (uses n - 1)."""
    return statistics.stdev(values)


def cv(values):
    """Return the coefficient of variation as a percentage."""
    mean = calculate_mean(values)
    if mean == 0:
        raise ValueError("Coefficient of variation is undefined when the mean is zero.")
    return (calculate_sample_std_dev(values) / mean) * 100


def calculate_cv(values):
    """Return the coefficient of variation as a percentage."""
    return cv(values)


def calculate_quartiles(values):
    """Return the first and third quartiles."""
    q1, q3 = np.percentile(values, [25, 75])
    return float(q1), float(q3)


def determine_skewness(values):
    """Classify skewness by comparing the mean and median."""
    mean = calculate_mean(values)
    median = calculate_median(values)

    if np.isclose(mean, median):
        return "Symmetric"
    if mean > median:
        return "Right-skewed"
    return "Left-skewed"


def interpret_cv(cv_percentage):
    """Classify variation using the thresholds given in the assignment."""
    if cv_percentage > 20:
        return "HIGH variation"
    if cv_percentage < 10:
        return "LOW variation"
    return "MODERATE variation"


def show_box_plot(values):
    """Display a box plot of quarterly sales revenue."""
    plt.boxplot(values)
    plt.title("Quarterly Sales Revenue")
    plt.ylabel("Revenue (thousands of dollars)")
    plt.xticks([1], ["Quarterly Sales"])
    plt.show()


def print_review(values):
    sorted_values = sorted(values)
    mean = calculate_mean(values)
    median = calculate_median(values)
    modes = calculate_mode(values)
    sample_std_dev = calculate_sample_std_dev(values)
    cv_percentage = calculate_cv(values)
    q1, q3 = calculate_quartiles(values)

    print(f"Dataset: {values}")
    print(f"Count: {len(values)}")

    print("\nGROUP A: Central Tendency")
    print(f"Sorted data: {sorted_values}")
    middle = len(sorted_values) // 2
    if len(sorted_values) % 2 == 0:
        print(
            "Middle values used for the median: "
            f"{sorted_values[middle - 1]} and {sorted_values[middle]}"
        )
    else:
        print(f"Middle value used for the median: {sorted_values[middle]}")
    print(f"Mean: {mean:.2f}")
    print(f"First-three-values mean check: {calculate_mean(values[:3]):.2f}")
    print(f"Median: {median:.2f}")
    if modes:
        formatted_modes = ", ".join(f"{mode:.2f}" for mode in modes)
        print(f"Mode(s): {formatted_modes}")
    else:
        print("Mode: No mode found.")

    print("\nGROUP B: Variation")
    print(f"Minimum: {min(values):.2f}")
    print(f"Maximum: {max(values):.2f}")
    print(f"Range: {calculate_range(values):.2f}")
    print(f"Sample standard deviation: {sample_std_dev:.2f}")
    print(f"Coefficient of variation: {cv_percentage:.2f}%")
    print(f"CV interpretation: {interpret_cv(cv_percentage)}")
    print("Squared-deviation examples:")
    print(f"  ({values[0]} - {mean:.2f})^2 = {(values[0] - mean) ** 2:.2f}")
    print(f"  ({values[1]} - {mean:.2f})^2 = {(values[1] - mean) ** 2:.2f}")

    print("\nGROUP C: Distribution Shape")
    print(f"Q1: {q1:.2f}")
    print(f"Q3: {q3:.2f}")
    print(f"IQR: {q3 - q1:.2f}")
    print(f"Skewness: {determine_skewness(values)}")

    print("\nFive-number summary")
    print(f"Minimum: {min(values):.2f}")
    print(f"Q1: {q1:.2f}")
    print(f"Median: {median:.2f}")
    print(f"Q3: {q3:.2f}")
    print(f"Maximum: {max(values):.2f}")

    print("\nBusiness summary")
    print(
        f"Quarterly revenue averages ${mean:.2f} thousand, with "
        f"{interpret_cv(cv_percentage).lower()} ({cv_percentage:.2f}% CV)."
    )
    print(
        "The mean is slightly above the median, so the assignment's comparison "
        "classifies the data as right-skewed."
    )


if __name__ == "__main__":
    print_review(data)
    show_box_plot(data)
