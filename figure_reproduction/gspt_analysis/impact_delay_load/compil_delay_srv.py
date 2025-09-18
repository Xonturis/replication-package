import matplotlib.pyplot as plt
from matplotlib import cm
import numpy as np

phones = (
    "S7",
    "S9",
    "S7 Tab FE",
    "S22",
)

phone_data_saas = {# S7 S9 S7Tab S22
    "SaaS Device": np.array([2.887,1.870,1.205,1.104]), # Average energy for iterations 2 - 5
    "SaaS Server": np.array([1.22,1.22,1.22,1.22]), # Server energy per request on SLA
    "SaaS Device Idle": np.array([0.14,0.18,0.2,0.13]), # Corresponding idle energy for devices
}

phone_err_saas = {# Error bars S7 S9 S7Tab S22
    "SaaS Device": np.array([0.1536553997512891,0.04525326535266779,0.11670225568583818,0.09081049862712462]),
    "SaaS Server": np.array([np.nan,np.nan,np.nan,np.nan]),
    "SaaS Device Idle": np.array([0.02784811833780915,0.041120785481830936,0.08361397534779913,0.0177040967247154]),
}

phone_data_lofi = {# S7 S9 S7Tab S22
    "LP Device": np.array([4.581,3.045,1.365,1.520]), # Average energy for iterations 2 - 5
}

phone_err_lofi = {# Error bars S7 S9 S7Tab S22
    "LP Device": np.array([0.22198196432829506,0.17957497764999544,0.121230618316055,0.08859847671715855]),
}

colors = ['tab:orange', cm.tab20c(6), cm.tab20c(7)]
i = 0

fig, ax = plt.subplots(figsize=(4.5,3))
bottom = np.zeros(4)
ax.grid(True, linestyle='--', alpha=0.5, zorder=0)

for i in range(len(phone_data_saas)):
    (measurment, phone_row) = list(phone_data_saas.items())[i]
    (_, errors) = list(phone_err_saas.items())[i]
    ax.barh(phones, phone_row, 0.3, align='edge', xerr=errors, ecolor="tab:grey", capsize=3, label=measurment, left=bottom, color=colors[i], zorder=3)
    bottom += phone_row

bottom = np.zeros(4)

(measurment_lofi, phone_row_lofi) = list(phone_data_lofi.items())[0]
(_, errors_lofi) = list(phone_err_lofi.items())[0]
ax.barh(phones, phone_row_lofi, -0.3, align='edge', xerr=errors_lofi, ecolor="tab:grey", capsize=3, label=measurment_lofi, left=bottom, color='tab:green', zorder=3)
bottom += phone_row

ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.set_xlabel("Energy for Step 4b (mWh)")
ax.set_ylabel("Phone Model")
ax.set_yticks(range(len(phones)), phones, rotation=90, va="center")

ax.legend(loc="upper right")

plt.tight_layout(pad=0)
# plt.show()
plt.savefig("final-energy.pdf")