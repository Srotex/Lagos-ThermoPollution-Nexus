import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from scipy.stats import linregress
from statsmodels.tsa.stattools import ccf
import pymannkendall as mk

# -----------------------
# Setup plotting style and folders
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

data_folder = r"C:\Users\clemo\Desktop\School\Article\Quantifying the Thermo Pollution Coupling LST AOD Dynamics in Lagos Metropolitan Area Nigeria\DATA"
output_folder = os.path.join(data_folder, "relationship_analysis", "correlation_analysis")
os.makedirs(output_folder, exist_ok=True)

# -----------------------
# Load datasets with error handling
# -----------------------
try:
    yearly_aod = pd.read_csv(os.path.join(data_folder, "Lagos_Yearly_AOD_2017_2025.csv"))
    yearly_lst = pd.read_csv(os.path.join(data_folder, "Lagos_Yearly_LST_2017_2025.csv"))
except Exception as e:
    raise RuntimeError(f"Error loading CSV files: {e}")

# -----------------------
# Merge datasets first, then add data completeness
# -----------------------
yearly = pd.merge(yearly_aod, yearly_lst, on="Year")

# Add data completeness note after merging
yearly['Data_Completeness'] = 'Complete'
yearly.loc[yearly['Year'] == 2025, 'Data_Completeness'] = 'Incomplete (Jan-Aug only)'

# Create versions with and without 2025 for different analyses
yearly_complete = yearly[yearly['Year'] < 2025].copy()  # For robust trend analysis
yearly_all = yearly.copy()  # For visualizations with notes

print(f"📊 Data Coverage: {yearly['Year'].min()}-{yearly['Year'].max()}")
print(f"   - Complete years: {yearly_complete['Year'].min()}-{yearly_complete['Year'].max()}")

# Check if 2025 exists and print its status
if 2025 in yearly['Year'].values:
    print(f"   - 2025 status: {yearly[yearly['Year'] == 2025]['Data_Completeness'].iloc[0]}")
else:
    print("   - 2025: No data")

# -----------------------
# Mann-Kendall trend detection + Sen's slope function
# -----------------------
def detect_trend(series, label, data_completeness="Complete"):
    if len(series) < 2:
        return {
            "Variable": label,
            "Trend": "Insufficient data",
            "p-value": np.nan,
            "Significance": "N/A",
            "Sen's Slope (/yr)": np.nan,
            "Data_Period": data_completeness
        }
    
    try:
        result = mk.original_test(series)
        slope = mk.sens_slope(series).slope

        if result.p <= 0.001:
            sig = "***"
        elif result.p <= 0.01:
            sig = "**"
        elif result.p <= 0.05:
            sig = "*"
        else:
            sig = "ns"

        return {
            "Variable": label,
            "Trend": result.trend,
            "p-value": result.p,
            "Significance": sig,
            "Sen's Slope (/yr)": slope,
            "Data_Period": data_completeness
        }
    except Exception as e:
        return {
            "Variable": label,
            "Trend": f"Error: {str(e)}",
            "p-value": np.nan,
            "Significance": "N/A",
            "Sen's Slope (/yr)": np.nan,
            "Data_Period": data_completeness
        }

# Calculate trends for both complete period and full period
trend_results = []

# Using complete data only (2017-2024) for robust trend analysis
if len(yearly_complete) >= 2:
    trend_results.append(detect_trend(yearly_complete["Mean_AOD"], "AOD", "2017-2024 (Complete)"))
    trend_results.append(detect_trend(yearly_complete["Mean_LST_Celsius"], "LST (°C)", "2017-2024 (Complete)"))

# Optional: Also calculate with 2025 included for comparison
if len(yearly_all) >= 2:
    trend_results.append(detect_trend(yearly_all["Mean_AOD"], "AOD", "2017-2025 (2025 Incomplete)"))
    trend_results.append(detect_trend(yearly_all["Mean_LST_Celsius"], "LST (°C)", "2017-2025 (2025 Incomplete)"))

trend_df = pd.DataFrame(trend_results)

# Save trend results styled table to Excel
try:
    styled_table = trend_df.style.format({
        "p-value": "{:.4f}" if trend_df['p-value'].notna().any() else "{:.0f}",
        "Sen's Slope (/yr)": "{:.4f}" if trend_df["Sen's Slope (/yr)"].notna().any() else "{:.0f}"
    }).set_table_styles([
        {'selector': 'th', 'props': [('font-weight', 'bold'), ('background-color', '#222'), ('color', 'white')]},
        {'selector': 'td', 'props': [('border', '1px solid #ccc')]}
    ]).hide(axis="index")
    styled_table.to_excel(os.path.join(output_folder, "trend_results_with_notes.xlsx"), index=False)
except Exception as e:
    print(f"Warning: Could not save trend results Excel: {e}")

# -----------------------
# Linear regression between Mean_AOD and Mean_LST_Celsius
# -----------------------
# Use complete data for regression to avoid bias from incomplete 2025
if len(yearly_complete) >= 2:
    try:
        slope, intercept, r_value, p_value, std_err = linregress(yearly_complete["Mean_AOD"], yearly_complete["Mean_LST_Celsius"])
        r_squared = r_value ** 2
        
        regression_success = True
    except Exception as e:
        print(f"Regression failed: {e}")
        regression_success = False
else:
    regression_success = False

if regression_success:
    # Save regression summary stats to Excel with data completeness note
    regression_summary = pd.DataFrame({
        "Statistic": ["Slope", "Intercept", "R-squared", "p-value", "Std Error", "Data_Period", "Note"],
        "Value": [slope, intercept, r_squared, p_value, std_err, "2017-2024", "Complete years only (2025 excluded due to incomplete data)"]
    })
    try:
        regression_summary.to_excel(os.path.join(output_folder, "regression_summary_with_notes.xlsx"), index=False)
    except Exception as e:
        print(f"Warning: Could not save regression summary Excel: {e}")
else:
    print("Warning: Insufficient data for regression analysis")
    # Create a placeholder regression summary
    regression_summary = pd.DataFrame({
        "Statistic": ["Slope", "Intercept", "R-squared", "p-value", "Std Error", "Data_Period", "Note"],
        "Value": [np.nan, np.nan, np.nan, np.nan, np.nan, "2017-2024", "Insufficient data for regression"]
    })
    regression_summary.to_excel(os.path.join(output_folder, "regression_summary_with_notes.xlsx"), index=False)

# -----------------------
# Plot scatter plot with regression line and R^2 annotation (top-right)
# -----------------------
print_colors = {
    "Mean_AOD": "#1f77b4",        # print-friendly blue
    "Mean_LST_Celsius": "#ff7f0e" # print-friendly orange
}

plt.figure(figsize=(8, 6), facecolor="#000000")
ax = plt.gca()
ax.set_facecolor("#000000")

# Plot complete years (2017-2024)
if len(yearly_complete) > 0:
    sns.scatterplot(
        data=yearly_complete,
        x="Mean_AOD",
        y="Mean_LST_Celsius",
        color=print_colors["Mean_AOD"],
        s=80,
        edgecolor="white",
        linewidth=1.2,
        alpha=0.85,
        label="2017-2024 (Complete)"
    )

# Plot 2025 with different style to indicate incomplete data
if 2025 in yearly_all['Year'].values:
    yearly_2025 = yearly_all[yearly_all['Year'] == 2025]
    sns.scatterplot(
        data=yearly_2025,
        x="Mean_AOD",
        y="Mean_LST_Celsius",
        color=print_colors["Mean_AOD"],
        s=120,  # Larger marker
        edgecolor="red",  # Red border to indicate caution
        linewidth=2.5,
        alpha=0.7,
        marker="X",  # Different marker
        label="2025 (Jan-Aug only)"
    )

# Regression line based on complete data only
if regression_success and len(yearly_complete) >= 2:
    x_vals = np.array(ax.get_xlim())
    y_vals = intercept + slope * x_vals
    ax.plot(x_vals, y_vals, color=print_colors["Mean_LST_Celsius"], lw=3, label="Regression Line (2017-2024)")
    
    # Add R² annotation
    textstr = f"R² = {r_squared:.3f}\n(2017-2024 only)"
    ax.text(0.02, 0.98, textstr, transform=ax.transAxes,
            fontsize=12, verticalalignment='top', horizontalalignment='left',
            color=print_colors["Mean_LST_Celsius"],
            bbox=dict(boxstyle="round,pad=0.5", facecolor="#000000cc",
                      edgecolor=print_colors["Mean_LST_Celsius"], linewidth=1.5))

ax.set_xlabel("Mean AOD", color="white", fontweight="bold")
ax.set_ylabel("Mean LST (°C)", color="white", fontweight="bold")

# Add title with data completeness note
if len(yearly_complete) > 0 and 2025 in yearly_all['Year'].values:
    plt.title("AOD vs LST Correlation (2017-2024 Complete Data)\n2025 shown for reference (incomplete)", 
              color="white", fontweight="bold", pad=20)
elif len(yearly_complete) > 0:
    plt.title("AOD vs LST Correlation (2017-2024 Complete Data)", 
              color="white", fontweight="bold", pad=20)
else:
    plt.title("AOD vs LST Correlation", color="white", fontweight="bold", pad=20)

ax.spines["bottom"].set_color("white")
ax.spines["left"].set_color("white")
ax.spines["top"].set_color("white")
ax.spines["right"].set_color("white")

ax.tick_params(colors="white", labelsize=12)
ax.grid(True, linestyle="--", alpha=0.3)

# Add legend if we have data
if len(yearly_complete) > 0 or 2025 in yearly_all['Year'].values:
    ax.legend(facecolor="#000000", edgecolor="white", framealpha=0.9, loc="lower right")

scatter_path = os.path.join(output_folder, "AOD_vs_LST_scatter_with_notes.png")
try:
    plt.savefig(scatter_path, dpi=300, facecolor=plt.gcf().get_facecolor())
except Exception as e:
    print(f"Warning: Could not save scatter plot: {e}")
plt.close()

# -----------------------
# Calculate residuals and CCF only if we have complete data and successful regression
# -----------------------
if regression_success and len(yearly_complete) >= 2:
    # Calculate residuals (observed LST minus predicted from AOD) - using complete data
    predicted_lst = intercept + slope * yearly_complete["Mean_AOD"]
    residuals = yearly_complete["Mean_LST_Celsius"] - predicted_lst

    # -----------------------
    # Cross-correlation function (CCF) using statsmodels - using complete data
    # -----------------------
    max_lag = min(3, len(yearly_complete) - 2)  # Reduced max_lag for smaller dataset

    # Standardize residuals and AOD for CCF
    resid_std = (residuals - residuals.mean()) / residuals.std()
    aod_std = (yearly_complete["Mean_AOD"] - yearly_complete["Mean_AOD"].mean()) / yearly_complete["Mean_AOD"].std()

    ccf_values = ccf(resid_std, aod_std)[:max_lag + 1]
    lags = np.arange(0, max_lag + 1)

    # -----------------------
    # Plot residuals and CCF side-by-side
    # -----------------------
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(9, 8), facecolor="#000000", sharex=False)
    fig.patch.set_alpha(1)

    # Residuals plot
    ax1.plot(yearly_complete["Year"], residuals, color=print_colors["Mean_LST_Celsius"], 
             marker='o', linestyle='-', linewidth=2, markersize=8)
    ax1.set_ylabel("Residuals (LST - Predicted)", color=print_colors["Mean_LST_Celsius"], fontweight="bold")
    ax1.tick_params(colors=print_colors["Mean_LST_Celsius"], labelsize=12)
    ax1.grid(True, linestyle="--", alpha=0.3)
    ax1.spines["bottom"].set_color("white")
    ax1.spines["left"].set_color(print_colors["Mean_LST_Celsius"])
    ax1.spines["top"].set_color("white")
    ax1.spines["right"].set_color("white")
    ax1.set_facecolor("#000000")
    ax1.set_title("Residuals Analysis (2017-2024 Complete Data)", color="white", fontweight="bold")

    # CCF stem plot
    markerline, stemlines, baseline = ax2.stem(lags, ccf_values, basefmt=" ", 
                                              linefmt=print_colors["Mean_AOD"], markerfmt='o')
    ax2.set_xlabel("Lag (years)", color="white", fontweight="bold")
    ax2.set_ylabel("CCF (Residuals vs AOD)", color=print_colors["Mean_AOD"], fontweight="bold")
    ax2.tick_params(colors=print_colors["Mean_AOD"], labelsize=12)
    ax2.grid(True, linestyle="--", alpha=0.3)
    ax2.spines["bottom"].set_color("white")
    ax2.spines["left"].set_color(print_colors["Mean_AOD"])
    ax2.spines["top"].set_color("white")
    ax2.spines["right"].set_color("white")
    ax2.set_facecolor("#000000")
    ax2.set_title("Cross-Correlation Function (2017-2024 Complete Data)", color="white", fontweight="bold")

    plt.setp(markerline, markerfacecolor=print_colors["Mean_AOD"], markeredgecolor=print_colors["Mean_AOD"])

    fig.tight_layout()

    ccf_plot_path = os.path.join(output_folder, "ccf_plot_with_notes.png")
    try:
        fig.savefig(ccf_plot_path, dpi=300, facecolor=fig.get_facecolor())
    except Exception as e:
        print(f"Warning: Could not save CCF plot: {e}")
    plt.close()
else:
    print("Warning: Skipping residuals and CCF analysis due to insufficient data")

# -----------------------
# Create data completeness report
# -----------------------
completeness_report = pd.DataFrame({
    'Analysis_Component': ['Trend Analysis', 'Regression Analysis', 'Residuals Analysis', 'CCF Analysis'],
    'Data_Period_Used': ['2017-2024 (Complete)', '2017-2024 (Complete)', '2017-2024 (Complete)', '2017-2024 (Complete)'],
    'Reason': ['Robust trend detection requires complete years', 
               'Avoid bias from incomplete 2025 data',
               'Consistency with regression period',
               'Adequate time series length for lag analysis'],
    '2025_Data_Status': ['Excluded', 'Excluded', 'Excluded', 'Excluded']
})

completeness_report.to_csv(os.path.join(output_folder, "analysis_data_completeness_report.csv"), index=False)

print(f"\n📋 Analysis Approach:")
print(completeness_report[['Analysis_Component', 'Data_Period_Used']].to_string(index=False))

print(f"\n🔥 Analysis complete. Results saved in:\n{output_folder}")
print("📝 Note: 2025 data (Jan-Aug only) was excluded from statistical analyses to maintain robustness")