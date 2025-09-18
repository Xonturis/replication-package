from scipy import stats
import numpy as np

SaaS = [2.887,1.870,1.205,1.104]
System = 1.22
SaaS_Idle = np.array(SaaS)+np.array([0.14,0.18,0.2,0.13]) # Add idle energy corresponding to the theoretical system energy for a given SLA

LoFi = [4.581, 3.045, 1.365, 1.52]  

# Calculate the differences
LmS = np.array(LoFi) - np.array(SaaS)  # This is the key dataset

# Perform the one-tailed paired t-test
t_stat, p_value = stats.ttest_rel(LoFi, SaaS, alternative='greater') # 'less' because we expect B < A

print(f"Paired t-test results:")
print(f"t-statistic: {t_stat:.3f}")
print(f"p-value: {p_value:.3f}")

# Also, print the mean difference for context
mean_difference = np.mean(LmS)
print(f"Mean energy difference (B - A): {mean_difference:.3f} (negative means B consumed more)")

print("--------- System wide breakeven diff")

# Calculate the breakeven difference for each device
breakeven_diffs = np.array(SaaS_Idle) - np.array(LoFi)

# Perform a one-sample t-test against the server cost.
# We use alternative='less' to test if the saving is LESS than the server cost.
t_stat, p_value = stats.ttest_1samp(breakeven_diffs, System, alternative='less')

print(f"One-sample t-test: Is the phone saving smaller than the server cost?")
print(f"t({len(breakeven_diffs)-1}) = {t_stat:.3f}, p = {p_value:.3f}")