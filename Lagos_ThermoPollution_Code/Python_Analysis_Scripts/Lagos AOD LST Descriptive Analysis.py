import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import os
from matplotlib.lines import Line2D

# -----------------------
# Setup
# -----------------------
sns.set_theme(style="darkgrid")
plt.rcParams.update({
    "font.size": 13,
    "axes.titlesize": 15,
    "axes.labelsize": 13,
    "legend.fontsize": 11,
    "xtick.labelsize": 11,
    "ytick.labelsize": 11,
    "axes.linewidth": 1.2,
    "lines.linewidth": 3,
    "lines.markersize": 10,
    "figure.facecolor": "#000000",
    "axes.facecolor": "#000000",
    "savefig.facecolor": "#000000",
    "axes.edgecolor": "white",
    "xtick.color": "white",
    "ytick.color": "white",
    "text.color": "white"
})

# -----------------------
# Folders
# -----------------------
data_folder = r"C:\Users\clemo\Desktop\School\Article\Quantifying the Thermo Pollution Coupling LST AOD Dynamics in Lagos Metropolitan Area Nigeria\DATA"
base_output_folder = os.path.join(data_folder, "analysis_results_badass")
output_folder = os.path.join(base_output_folder, "descriptive_analysis")
os.makedirs(output_folder, exist_ok=True)

# -----------------------
# Load datasets
# -----------------------
files = {
    "monthly_aod": "Lagos_Monthly_AOD_2017_2025.csv",
    "monthly_lst": "Lagos_Monthly_LST_2017_2025.csv",
    "seasonal_aod": "Lagos_Seasonal_AOD_2017_2025.csv",
    "seasonal_lst": "Lagos_Seasonal_LST_2017_2025.csv",
    "yearly_aod": "Lagos_Yearly_AOD_2017_2025.csv",
    "yearly_lst": "Lagos_Yearly_LST_2017_2025.csv"
}

dfs = {}
for key, fname in files.items():
    path = os.path.join(data_folder, fname)
    dfs[key] = pd.read_csv(path)

# -----------------------
# Merge datasets and add Date columns
# -----------------------

# Monthly
monthly = pd.merge(dfs["monthly_aod"], dfs["monthly_lst"], on=["Month", "Year"])
monthly['Date'] = pd.to_datetime(monthly[['Year', 'Month']].assign(DAY=1))

# Seasonal
seasonal = pd.merge(dfs["seasonal_aod"], dfs["seasonal_lst"], on=["Season", "Year"])
seasonal['Season'] = seasonal['Season'].str.strip().str.upper()
season_order_map = {
    'DRY_SEASON': 1,
    'WET_SEASON': 2,
    'DJF': 1,
    'MAM': 2,
    'JJA': 3,
    'SON': 4
}
seasonal['Season_Order'] = seasonal['Season'].map(season_order_map)
seasonal = seasonal.dropna(subset=['Season_Order'])
seasonal = seasonal.sort_values('Season_Order')
seasonal['Date'] = pd.to_datetime(seasonal['Year'].astype(str) + '-01-01') + pd.to_timedelta((seasonal['Season_Order']-1)*3*30, unit='D')

# Yearly
yearly = pd.merge(dfs["yearly_aod"], dfs["yearly_lst"], on=["Year"])
yearly['Year'] = yearly['Year'].astype(int)
yearly['Date'] = pd.to_datetime(yearly['Year'].astype(str) + '-01-01')

# -----------------------
# Data validation - missing values
# -----------------------
print("Missing values in monthly merged data:\n", monthly.isnull().sum())
print("Missing values in seasonal merged data:\n", seasonal.isnull().sum())
print("Missing values in yearly merged data:\n", yearly.isnull().sum())

# -----------------------
# Summary stats function
# -----------------------
def get_summary(df, value_cols):
    summary = {}
    for col in value_cols:
        summary[col] = {
            "Mean": df[col].mean(),
            "Min": df[col].min(),
            "Max": df[col].max(),
            "Std Dev": df[col].std()
        }
    return pd.DataFrame(summary).T

# Create summaries
monthly_summary = get_summary(monthly, ["Mean_AOD", "Mean_LST_Celsius"])
seasonal_summary = get_summary(seasonal, ["Mean_AOD", "Mean_LST_Celsius"])
yearly_summary = get_summary(yearly, ["Mean_AOD", "Mean_LST_Celsius"])

# Save summaries
monthly_summary.to_csv(os.path.join(output_folder, "monthly_summary.csv"))
seasonal_summary.to_csv(os.path.join(output_folder, "seasonal_summary.csv"))
yearly_summary.to_csv(os.path.join(output_folder, "yearly_summary.csv"))

print("✅ Summary tables saved in:", output_folder)

# -----------------------
# Prepare aggregated data for plots
# -----------------------
monthly_cycle = monthly.groupby("Month")[["Mean_AOD", "Mean_LST_Celsius"]].mean().reset_index()
seasonal_cycle = seasonal.groupby(["Season", "Season_Order"])[["Mean_AOD", "Mean_LST_Celsius"]].mean().reset_index()
seasonal_cycle = seasonal_cycle.sort_values('Season_Order')

# -----------------------
# 1. Monthly Cycle Line Plot (AOD & LST) with subdued colors and peak callouts for both (AOD left, LST right)
# -----------------------
fig, ax1 = plt.subplots(figsize=(10, 6), facecolor="#000000")
fig.patch.set_alpha(1)

color_aod = "#1f77b4"  # subdued blue for AOD
color_lst = "#ff7f0e"  # subdued orange for LST

ax1.plot(monthly_cycle["Month"], monthly_cycle["Mean_AOD"],
         marker="o", linestyle="-", color=color_aod,
         label="Mean AOD", alpha=0.85, markeredgecolor="black", markeredgewidth=1.5)
ax1.set_ylabel("Mean AOD", color=color_aod, fontweight="bold")
ax1.tick_params(axis='y', colors=color_aod, labelsize=13)
ax1.set_xlabel("Month", color="white", fontweight="bold")
ax1.set_xticks(np.arange(1, 13))
ax1.set_xlim(1, 12)
ax1.grid(which="major", axis="y", linestyle="--", alpha=0.3)

# Adjust spines color
ax1.spines['bottom'].set_color('white')
ax1.spines['left'].set_color(color_aod)
ax1.spines['top'].set_color('white')
ax1.spines['right'].set_color(color_lst)

ax2 = ax1.twinx()
ax2.plot(monthly_cycle["Month"], monthly_cycle["Mean_LST_Celsius"],
         marker="s", linestyle="--", color=color_lst,
         label="Mean LST (°C)", alpha=0.85, markeredgecolor="black", markeredgewidth=1.5)
ax2.set_ylabel("Mean LST (°C)", color=color_lst, fontweight="bold")
ax2.tick_params(axis='y', colors=color_lst, labelsize=13)

# Legend top right with black bg and white edge
lines1, labels1 = ax1.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax1.legend(lines1 + lines2, labels1 + labels2, loc="upper right", fontsize=13,
           facecolor="#000000", edgecolor="white", framealpha=0.9)

# Peak indices & values for callouts
peak_aod_idx = monthly_cycle["Mean_AOD"].idxmax()
peak_aod_month = monthly_cycle.loc[peak_aod_idx, "Month"]
peak_aod_value = monthly_cycle.loc[peak_aod_idx, "Mean_AOD"]

peak_lst_idx = monthly_cycle["Mean_LST_Celsius"].idxmax()
peak_lst_month = monthly_cycle.loc[peak_lst_idx, "Month"]
peak_lst_value = monthly_cycle.loc[peak_lst_idx, "Mean_LST_Celsius"]

# Draw vertical line at LST peak month
ax2.axvline(x=peak_lst_month, color=color_lst, linestyle="--", lw=2, alpha=0.7)

# Callout for peak AOD (left side), Y-position fixed to 1.3 so it doesn't cover actual peak
x_callout_left = peak_aod_month - 0.3
ax1.text(x_callout_left, 1.3,
         f"Peak AOD: {peak_aod_value:.2f}",
         fontsize=12,
         color=color_aod,
         fontweight="bold",
         bbox=dict(boxstyle="round,pad=0.3", fc="#000000cc", ec=color_aod, lw=2),
         ha='right',
         va='bottom')

# Callout for peak LST (right side)
x_callout_right = peak_lst_month + 0.3
ax2.text(x_callout_right, peak_lst_value,
         f"Peak LST: {peak_lst_value:.1f} °C",
         fontsize=12,
         color=color_lst,
         fontweight="bold",
         bbox=dict(boxstyle="round,pad=0.3", fc="#000000cc", ec=color_lst, lw=2),
         ha='left',
         va='center')

fig.tight_layout()
fig.savefig(os.path.join(output_folder, "Monthly_Cycle_AOD_and_LST.png"), dpi=300, facecolor=fig.get_facecolor())
plt.close()

# -----------------------
# 2. Seasonal Cycle Plot (clean, no callouts)
# -----------------------
fig, ax1 = plt.subplots(figsize=(9, 6), facecolor="#000000")
fig.patch.set_alpha(1)

bar_color = "#1f77b4"  # subdued blue for AOD bars
line_color = "#ff7f0e" # subdued orange for LST line

bars = ax1.bar(seasonal_cycle["Season"], seasonal_cycle["Mean_AOD"], alpha=0.85,
               color=bar_color, edgecolor="black", linewidth=1.7, label="Mean AOD")
ax1.set_ylabel("Mean AOD", color=bar_color, fontweight="bold")
ax1.tick_params(axis='y', colors=bar_color, labelsize=13)
ax1.set_xlabel("Season", color="white", fontweight="bold")

ax1.spines['bottom'].set_color('white')
ax1.spines['left'].set_color(bar_color)
ax1.spines['top'].set_color('white')
ax1.spines['right'].set_color(line_color)

ax2 = ax1.twinx()
ax2.plot(seasonal_cycle["Season"], seasonal_cycle["Mean_LST_Celsius"],
         marker="D", markersize=11, linestyle="-", color=line_color,
         linewidth=3, label="Mean LST (°C)", markeredgewidth=2, markeredgecolor='black')
ax2.set_ylabel("Mean LST (°C)", color=line_color, fontweight="bold")
ax2.tick_params(axis='y', colors=line_color, labelsize=13)

ax2.spines['right'].set_color(line_color)
ax2.spines['left'].set_color(bar_color)

legend_elements = [
    Line2D([0], [0], color=bar_color, lw=8, label='Mean AOD'),
    Line2D([0], [0], color=line_color, lw=3, label='Mean LST (°C)', marker='D', markersize=10,
           markeredgecolor='black', markeredgewidth=1.8)
]
ax1.legend(handles=legend_elements, loc='upper right', fontsize=13,
           facecolor="#000000", edgecolor="white", framealpha=0.9)

ax1.grid(axis="y", alpha=0.3)
fig.tight_layout()
fig.savefig(os.path.join(output_folder, "Seasonal_Cycle_AOD_and_LST.png"), dpi=300, facecolor=fig.get_facecolor())
plt.close()

print("🔥 All descriptive analysis outputs saved in:", output_folder)