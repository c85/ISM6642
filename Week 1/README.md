Descriptive Statistics: 45-Minute Peer Programming Lab

📊 Descriptive Statistics: 45-Minute Peer Programming Lab

Course: Statistics for Management (Lesson 3)
Format: In-Class Peer Programming Lab
Time Allocation: 45 minutes

📌 Assignment Overview

This is a fast-paced, in-class peer programming lab. Teams of 2–3 students will work for 45 minutes to calculate and interpret a specific group of descriptive statistics. Each team focuses on ONE statistic group for discussion; but will attempt solving all Groups below;  groups will share their findings at the end of class. All team members submit online at the end.

⏰ 45-Minute Agenda

Time	Activity
0–2 min	Instructor introduces lab. Assign groups and statistic groups. Hand out this sheet.
2–5 min	Teams review their statistic group. Discuss approach and algorithm. Designate first driver/navigator.
5–30 min	CODING SPRINT. Teams swap driver/navigator every 10 minutes. Implement calculations, test, verify results.
30–38 min	Finish up. Prepare 2-minute verbal summary of findings. Create one quick visualization or summary table if time permits.
38–45 min	Debrief. Each group shares 2-minute summary. Class discusses insights. Instructor collects code files.
👥 Your Group Info

Group Members: ___________________, ___________________, ___________________

Focus Statistic Group:

☐ Central Tendency
☐ Variation
☐ Distribution Shape
Peer Programming Roles

Driver: Types code. Focus on implementation.
Navigator: Reviews code in real-time. Refers to formulas. Suggests improvements. Catches errors.
Rotation: Swap every 10 minutes. All team members must drive at least once.
📈 Dataset (All Groups Use This)

Sales Revenue per Quarter (in thousands, $):

45, 52, 48, 61, 55, 49, 58, 63, 51, 47, 59, 64

💻 Starter Code

Copy & paste this to begin:

import numpy as np
import statistics

# Dataset
data = [45, 52, 48, 61, 55, 49, 58, 63, 51, 47, 59, 64]

# Print basics
print(f"Dataset: {data}")
print(f"Count: {len(data)}")

# TODO: Add your statistic functions here →
🎯 Your Task (Choose Your Group)

GROUP A: Central Tendency (Mean, Median, Mode)

Calculate these three measures for the sales dataset. Show all results with 2 decimal places.

Mean

Formula: Σ xᵢ / n

Implement: def calculate_mean(data): return sum(data) / len(data)
Manual check: Add first 3 values by hand, divide by 3.
Median

Definition: Middle value when sorted

Implement: Use statistics.median() OR sort manually and find middle.
Show: The sorted array and circle the middle value.
Mode

Definition: Most frequent value

Implement: Use statistics.mode() OR count occurrences manually.
Note: If no mode exists, say "No mode found."
GROUP B: Variation (Range, Std Dev, CV)

Calculate these three measures for the sales dataset.

Range

Formula: Max − Min

Implement: def calculate_range(data): return max(data) - min(data)
Identify: What is the min? What is the max?
Sample Standard Deviation

Formula: √[Σ(xᵢ − x̄)² / (n − 1)]

Implement: Use np.std(data, ddof=1) OR statistics.stdev(data)
Manual: Calculate mean first. Show (x₁ − mean)² and (x₂ − mean)² as examples.
Coefficient of Variation (CV)

Formula: (StdDev / Mean) × 100%

Implement: def cv(data): return (statistics.stdev(data) / statistics.mean(data)) * 100
Interpret: Is CV > 20%? If yes, variation is HIGH. If < 10%, LOW.
GROUP C: Distribution Shape (Quartiles & Skewness)

Calculate Q1, Q3 and determine skewness (symmetric vs. skewed).

Q1 and Q3

Definition: 25th and 75th percentiles

Implement: Use np.percentile(data, 25) and np.percentile(data, 75)
Show: IQR = Q3 − Q1
Skewness Check

Compare Mean vs. Median:

If Mean ≈ Median → Symmetric
If Mean > Median → Right-Skewed (tail on right)
If Mean < Median → Left-Skewed (tail on left)
Visualize (Bonus)

If time permits:

Create a simple box plot: plt.boxplot(data); plt.show()
Or print a 5-number summary: min, Q1, median, Q3, max
📤 What to Turn In

Python code file (.py) with working functions and output
2-minute verbal summary of your findings (be ready to present!)
One quick result summary or visualization (even a printed table is fine)
✨ Quick Tips for Success

Start coding NOW. Don't overthink the algorithm—talk it through in 1 minute, then code.
Swap driver/navigator every 10 minutes. Use a phone timer.
Test early. Run your code after each function with print() statements.
Compare to known values. For the first 3 values: 45, 52, 48. Mean should be 48.33.
Ask for help. Raise your hand; instructor and peers are here to support.
Use libraries (numpy, statistics). Manual implementation is encouraged but not required in 45 min.
📊 Quick Grading (Out of 10 Points -scaled to 100 points)

Criterion	Points
Working code (runs without errors)	4
Correct calculations (values are accurate)	3
Peer programming & communication (roles, swaps, explanation)	2
Summary/visualization or verbal presentation	1
🎤 Debrief Questions (Instructor Leads Discussion)

Group A: How does the mean compare to the median? Why might they differ?
Group B: What does the CV of ~10% tell us about consistency in quarterly sales? What are the business implications?
Group C: Is the sales data symmetric or skewed? What does that suggest for business planning? 
All: What was the biggest challenge during peer programming? What worked well?
🚀 Ready to Code? Form your groups, choose your roles, and let's get started!

Remember: communication is key. Talk through the algorithm first, then code. Good luck!