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

### Box Plot Interpretation

The box plot summarizes the center and spread of quarterly sales. The line inside the box represents the **$53.50 thousand median**. The box extends from **Q1 at $48.75 thousand** to **Q3 at $59.50 thousand**, so the middle 50% of quarterly sales falls within this range. The box's length represents an **IQR of $10.75 thousand**.

The whiskers extend to the minimum of **$45 thousand** and the maximum of **$64 thousand**. Using the 1.5 × IQR rule gives a lower outlier boundary of $32.63 thousand and an upper boundary of $75.63 thousand. All observations fall within these boundaries, so the plot shows **no apparent outliers**.

The median is reasonably close to the center of the box, and the two whiskers have similar lengths. This suggests a fairly balanced distribution. However, the upper half of the box and upper whisker are slightly longer, supporting the conclusion that the data is **slightly right-skewed rather than strongly skewed**. For business planning, the absence of outliers suggests that the observed quarterly results are reasonably stable and that no single extreme quarter is distorting the overall pattern.

## All Groups: Peer Programming Reflection

The biggest challenge was keeping the driver and navigator synchronized while translating statistical formulas into correct code under a time limit. It was also important to agree on details such as using the sample standard deviation and interpreting a CV near a category boundary.

What worked well was discussing each formula before coding, testing one function at a time, and checking the program's results against simple manual calculations. Christopher focused on implementation as the driver, while John reviewed the work as the navigator. Both members then reviewed the final output together.

### Team Roles, Communication, and Final Review

- **Christopher Martin — Driver:** Entered and ran the Python code, implemented the statistical calculations, and generated the box plot.
- **John Marin — Navigator:** Reviewed the code and formulas as they were implemented, checked the logic, and helped verify that the results matched the assignment requirements.
- **Final-output review:** After completing their primary roles, Christopher and John both acted as observers of the final output. They reviewed the printed statistics and box plot together, discussed their meaning, and confirmed that the results and explanations were consistent.

The team communicated by explaining the approach before implementation and discussing the output after each calculation. Instead of exchanging the driver and navigator positions during the final review, both members moved into an observer/reviewer role so they could jointly validate the completed work.
