# 📊 Descriptive Statistics: 45-Minute Peer Programming Lab

- **Course:** Statistics for Management (Lesson 3)
- **Format:** In-Class Peer Programming Lab
- **Time Allocation:** 45 minutes

## 📌 Assignment Overview

This is a fast-paced, in-class peer programming lab. Teams of 2–3 students will work for 45 minutes to calculate and interpret a specific group of descriptive statistics. Each team focuses on **one** statistic group for discussion but will attempt to solve all groups below. Groups will share their findings at the end of class, and all team members will submit online.

## ⏰ 45-Minute Agenda

| Time | Activity |
| --- | --- |
| 0–2 min | Instructor introduces the lab, assigns teams and statistic groups, and hands out this sheet. |
| 2–5 min | Teams review their statistic group, discuss their approach and algorithm, and designate the first driver and navigator. |
| 5–30 min | **Coding sprint:** Teams swap driver and navigator every 10 minutes. Implement calculations, test, and verify results. |
| 30–38 min | Finish up and prepare a two-minute verbal summary of findings. Create one quick visualization or summary table if time permits. |
| 38–45 min | **Debrief:** Each group shares a two-minute summary. The class discusses insights, and the instructor collects code files. |

## 👥 Your Group Information

**Group Members:** ___________________, ___________________, ___________________

**Focus Statistic Group:**

- [ ] Central Tendency
- [ ] Variation
- [ ] Distribution Shape

### Peer Programming Roles

- **Driver:** Types code and focuses on implementation.
- **Navigator:** Reviews code in real time, refers to formulas, suggests improvements, and catches errors.
- **Rotation:** Swap every 10 minutes. All team members must drive at least once.

## 📈 Dataset

All groups will use the following sales revenue per quarter, measured in thousands of dollars:

```text
45, 52, 48, 61, 55, 49, 58, 63, 51, 47, 59, 64
```

## 💻 Starter Code

Copy and paste this code to begin:

```python
import numpy as np
import statistics

# Dataset
data = [45, 52, 48, 61, 55, 49, 58, 63, 51, 47, 59, 64]

# Print basics
print(f"Dataset: {data}")
print(f"Count: {len(data)}")

# TODO: Add your statistic functions here →
```

## 🎯 Your Task

### Group A: Central Tendency (Mean, Median, and Mode)

Calculate the following three measures for the sales dataset. Show all results with two decimal places.

#### Mean

- **Formula:** Σxᵢ / n
- **Implementation:** `def calculate_mean(data): return sum(data) / len(data)`
- **Manual check:** Add the first three values by hand, then divide by 3.

#### Median

- **Definition:** The middle value when the data is sorted.
- **Implementation:** Use `statistics.median()`, or sort the data manually and find the middle.
- **Show:** The sorted array with the middle value identified.

#### Mode

- **Definition:** The most frequent value.
- **Implementation:** Use `statistics.mode()`, or count occurrences manually.
- **Note:** If no mode exists, state, "No mode found."

### Group B: Variation (Range, Standard Deviation, and CV)

Calculate the following three measures for the sales dataset.

#### Range

- **Formula:** Maximum − Minimum
- **Implementation:** `def calculate_range(data): return max(data) - min(data)`
- **Identify:** What are the minimum and maximum values?

#### Sample Standard Deviation

- **Formula:** √[Σ(xᵢ − x̄)² / (n − 1)]
- **Implementation:** Use `np.std(data, ddof=1)` or `statistics.stdev(data)`.
- **Manual check:** Calculate the mean first. Show `(x₁ − mean)²` and `(x₂ − mean)²` as examples.

#### Coefficient of Variation (CV)

- **Formula:** (Standard Deviation / Mean) × 100%
- **Implementation:** `def cv(data): return (statistics.stdev(data) / statistics.mean(data)) * 100`
- **Interpretation:** If CV > 20%, variation is **high**. If CV < 10%, variation is **low**.

### Group C: Distribution Shape (Quartiles and Skewness)

Calculate Q1 and Q3, then determine whether the distribution is symmetric or skewed.

#### Q1 and Q3

- **Definition:** The 25th and 75th percentiles.
- **Implementation:** Use `np.percentile(data, 25)` and `np.percentile(data, 75)`.
- **Show:** IQR = Q3 − Q1.

#### Skewness Check

Compare the mean and median:

- **Mean ≈ Median:** Symmetric
- **Mean > Median:** Right-skewed (tail on the right)
- **Mean < Median:** Left-skewed (tail on the left)

#### Visualization (Bonus)

If time permits:

- Create a simple box plot using `plt.boxplot(data); plt.show()`.
- Or print a five-number summary: minimum, Q1, median, Q3, and maximum.

## 📤 What to Turn In

- A Python code file (`.py`) with working functions and output.
- A two-minute verbal summary of your findings—be ready to present.
- One quick result summary or visualization; a printed table is acceptable.

## ✨ Quick Tips for Success

- **Start coding now.** Do not overthink the algorithm—talk it through in one minute, then code.
- **Swap driver and navigator every 10 minutes.** Use a phone timer.
- **Test early.** Run your code after each function using `print()` statements.
- **Compare with known values.** For the first three values—45, 52, and 48—the mean should be 48.33.
- **Ask for help.** Raise your hand; the instructor and your peers are available to support you.
- **Use libraries.** Manual implementation is encouraged but not required within the 45-minute lab.

## 📊 Quick Grading (10 Points, Scaled to 100)

| Criterion | Points |
| --- | ---: |
| Working code that runs without errors | 4 |
| Correct and accurate calculations | 3 |
| Peer programming and communication, including roles, swaps, and explanation | 2 |
| Summary, visualization, or verbal presentation | 1 |
| **Total** | **10** |

## 🎤 Debrief Questions

- **Group A:** How does the mean compare with the median? Why might they differ?
- **Group B:** What does a CV of approximately 10% tell us about consistency in quarterly sales? What are the business implications?
- **Group C:** Is the sales data symmetric or skewed? What does that suggest for business planning?
- **All Groups:** What was the biggest challenge during peer programming? What worked well?

## 🚀 Ready to Code?

Form your groups, choose your roles, and get started.

Remember: communication is key. Talk through the algorithm first, then code. Good luck!
