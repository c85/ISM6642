# Descriptive Statistics Peer Programming Debrief

## Group A: Mean Compared with the Median

The mean quarterly sales revenue is **$54.33 thousand**, while the median is **$53.50 thousand**. The mean is therefore **$0.83 thousand higher** than the median.

They differ because the mean uses every value and is more sensitive to unusually high or low observations. In this dataset, higher sales values such as $61,000, $63,000, and $64,000 pull the mean slightly above the median. The median depends only on the middle two values after sorting, so it is less affected by those higher quarters.

## Group B: Coefficient of Variation and Sales Consistency

The calculated coefficient of variation is **12.09%**, which is reasonably close to the approximately 10% value referenced in the question. This means the sample standard deviation is about 12% of average quarterly sales. Quarterly performance is therefore fairly consistent, although there is still moderate variation from one quarter to another.

For the business, this level of consistency makes revenue, staffing, inventory, and cash-flow planning more predictable. Managers can use the $54.33 thousand mean as a useful baseline, but they should retain some flexibility because quarterly sales can still move above or below that level. They should also investigate whether the variation follows a seasonal pattern before assuming every quarter will perform similarly.

## Group C: Distribution Shape and Business Planning

The data is **slightly right-skewed** according to the assignment's comparison rule because the mean ($54.33 thousand) is a little higher than the median ($53.50 thousand). This indicates that a few stronger quarters pull the average upward. Because the difference is small, the distribution is close to symmetric rather than strongly skewed.

For planning, managers should avoid treating the mean as a guaranteed result because it is influenced by the highest-sales quarters. Using both the mean and median provides a more balanced forecast. The median is a reasonable conservative baseline, while the higher observations can inform an optimistic scenario for inventory, staffing, and revenue targets.

## All Groups: Peer Programming Reflection

The biggest challenge was keeping the driver and navigator synchronized while translating statistical formulas into correct code, especially when switching roles under a time limit. It was also important to agree on details such as using the sample standard deviation and interpreting a CV near a category boundary.

What worked well was discussing each formula before coding, testing one function at a time, and checking the program's results against simple manual calculations. The navigator helped catch errors and question assumptions, while rotating roles gave each team member experience implementing and reviewing the solution.
