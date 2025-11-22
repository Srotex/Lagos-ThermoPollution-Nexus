import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from scipy.stats import pearsonr, spearmanr
from sklearn.linear_model import LinearRegression
from statsmodels.tsa.seasonal import STL
import pmdarima as pm
from statsmodels.tsa.statespace.sarimax import SARIMAX
import warnings

warnings.filterwarnings("ignore")

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

colors = {
    "observed": "#1f77b4",
    "predicted": "#ff7f0e"
}

data_folder = r"C:\Users\clemo\Desktop\School\Article\Quantifying the Thermo Pollution Coupling LST AOD Dynamics in Lagos Metropolitan Area Nigeria\DATA"
base_output_folder = os.path.join(data_folder, "analysis_results_badass")
relationship_folder = os.path.join(base_output_folder, "relationship_analysis")
modeling_folder = os.path.join(base_output_folder, "modeling_analysis")
os.makedirs(relationship_folder, exist_ok=True)
os.makedirs(modeling_folder, exist_ok=True)

try:
    monthly_aod = pd.read_csv(os.path.join(data_folder, "Lagos_Monthly_AOD_2017_2025.csv"))
    monthly_lst = pd.read_csv(os.path.join(data_folder, "Lagos_Monthly_LST_2017_2025.csv"))
except Exception as e:
    raise RuntimeError(f"Error loading CSV files: {e}")

monthly = pd.merge(monthly_aod, monthly_lst, on=["Year", "Month"])
monthly.sort_values(["Year", "Month"], inplace=True)
monthly.dropna(subset=["Mean_AOD", "Mean_LST_Celsius"], inplace=True)
monthly['Date'] = pd.to_datetime(monthly[['Year', 'Month']].assign(DAY=1))
monthly.set_index('Date', inplace=True)

def correlation_tests(x, y, label_x, label_y):
    pearson_r, pearson_p = pearsonr(x, y)
    spearman_r, spearman_p = spearmanr(x, y)
    def stars(p):
        return "***" if p <= 0.001 else "**" if p <= 0.01 else "*" if p <= 0.05 else "ns"
    return {
        "X": label_x,
        "Y": label_y,
        "Pearson r": pearson_r,
        "Pearson p": pearson_p,
        "Pearson sig": stars(pearson_p),
        "Spearman rho": spearman_r,
        "Spearman p": spearman_p,
        "Spearman sig": stars(spearman_p)
    }

rel_results = []
rel_results.append(correlation_tests(monthly["Mean_AOD"], monthly["Mean_LST_Celsius"], "AOD", "LST (°C)"))

max_lag = 3
for lag in range(1, max_lag + 1):
    rel_results.append(correlation_tests(
        monthly["Mean_AOD"][:-lag].values,
        monthly["Mean_LST_Celsius"][lag:].values,
        f"AOD (lead {lag} mo)", "LST (°C)"
    ))
    rel_results.append(correlation_tests(
        monthly["Mean_AOD"][lag:].values,
        monthly["Mean_LST_Celsius"][:-lag].values,
        f"AOD (lag {lag} mo)", "LST (°C)"
    ))

rel_df = pd.DataFrame(rel_results)
try:
    rel_df.to_excel(os.path.join(relationship_folder, "relationship_analysis.xlsx"), index=False)
except Exception as e:
    print(f"Warning: Could not save relationship_analysis.xlsx: {e}")

plt.figure(figsize=(8, 6), facecolor="#000000")
ax = plt.gca()
ax.set_facecolor("#000000")

sns.regplot(data=monthly, x="Mean_AOD", y="Mean_LST_Celsius",
            scatter_kws={"s": 60, "alpha": 0.85, "edgecolor": "white", "linewidths": 1.2},
            line_kws={"color": colors["predicted"], "lw": 3},
            ax=ax)

r, p = pearsonr(monthly["Mean_AOD"], monthly["Mean_LST_Celsius"])

# Moved annotation to top right corner:
textstr = f"Pearson r = {r:.3f}\nR² = {r**2:.3f}\np = {p:.4f}"
ax.text(0.98, 0.98, textstr, transform=ax.transAxes,
        fontsize=12, verticalalignment='top', horizontalalignment='right',
        color=colors["predicted"],
        bbox=dict(boxstyle="round,pad=0.5", facecolor="#000000cc", edgecolor=colors["predicted"], linewidth=2))

ax.set_xlabel("Mean AOD", color="white", fontweight="bold")
ax.set_ylabel("Mean LST (°C)", color=colors["predicted"], fontweight="bold")

for spine in ["bottom", "left", "top", "right"]:
    ax.spines[spine].set_color("white" if spine in ["bottom","top"] else colors["predicted"])

ax.tick_params(colors="white", labelsize=12)
ax.grid(True, linestyle="--", alpha=0.3)
plt.tight_layout()

scatter_filename = "AOD_vs_LST_scatter.png"
try:
    plt.savefig(os.path.join(relationship_folder, scatter_filename), dpi=300, facecolor=plt.gcf().get_facecolor())
except Exception as e:
    print(f"Warning: Could not save scatter plot: {e}")
plt.close()

X = monthly["Mean_AOD"].values.reshape(-1, 1)
y = monthly["Mean_LST_Celsius"].values

model = LinearRegression()
model.fit(X, y)
y_pred = model.predict(X)
residuals = y - y_pred

plt.figure(figsize=(8, 4), facecolor="#000000")
ax = plt.gca()
ax.set_facecolor("#000000")

plt.scatter(y_pred, residuals, alpha=0.85, edgecolor="white", linewidth=1.2, color=colors["predicted"])
plt.axhline(0, color=colors["predicted"], linestyle="--", linewidth=2)
plt.xlabel("Fitted values (Predicted LST)", color="white", fontweight="bold")
plt.ylabel("Residuals", color=colors["predicted"], fontweight="bold")
plt.grid(True, linestyle="--", alpha=0.3)

for spine in ["bottom", "left", "top", "right"]:
    ax.spines[spine].set_color("white" if spine in ["bottom","top"] else colors["predicted"])

ax.tick_params(colors="white", labelsize=12)
plt.tight_layout()

residuals_filename = "regression_residuals.png"
try:
    plt.savefig(os.path.join(relationship_folder, residuals_filename), dpi=300, facecolor=plt.gcf().get_facecolor())
except Exception as e:
    print(f"Warning: Could not save residuals plot: {e}")
plt.close()

# SARIMAX model tuning and fitting
ts = monthly["Mean_LST_Celsius"]
sarimax_orders_file = os.path.join(modeling_folder, "SARIMAX_orders.txt")

try:
    print("Running auto_arima to select SARIMAX orders. This may take some time...")
    stepwise_model = pm.auto_arima(ts,
                                   seasonal=True,
                                   m=12,
                                   trace=True,
                                   error_action='ignore',
                                   suppress_warnings=True,
                                   stepwise=True)
    orders = {
        "order": stepwise_model.order,
        "seasonal_order": stepwise_model.seasonal_order
    }
    with open(sarimax_orders_file, "w") as f:
        f.write("Optimal SARIMAX model orders found by auto_arima:\n")
        f.write(f"ARIMA order (p,d,q): {orders['order']}\n")
        f.write(f"Seasonal order (P,D,Q,m): {orders['seasonal_order']}\n")
except Exception as e:
    print(f"auto_arima failed with error: {e}. Using fallback orders (1,1,1)(0,1,1,12)")
    orders = {
        "order": (1, 1, 1),
        "seasonal_order": (0, 1, 1, 12)
    }
    with open(sarimax_orders_file, "w") as f:
        f.write("Fallback SARIMAX orders due to auto_arima failure:\n")
        f.write(f"ARIMA order (p,d,q): {orders['order']}\n")
        f.write(f"Seasonal order (P,D,Q,m): {orders['seasonal_order']}\n")

try:
    sarimax_model = SARIMAX(ts, order=orders["order"], seasonal_order=orders["seasonal_order"],
                           enforce_stationarity=False, enforce_invertibility=False)
    sarimax_results = sarimax_model.fit(disp=False)
except Exception as e:
    print(f"Error fitting SARIMAX model: {e}")
    sarimax_results = None

# STL decomposition and plots
try:
    stl = STL(ts, seasonal=13, robust=True)
    stl_result = stl.fit()

    # Trend
    plt.figure(figsize=(10, 4), facecolor="#000000")
    ax = plt.gca()
    ax.set_facecolor("#000000")
    ax.plot(ts.index, stl_result.trend, color=colors["predicted"], lw=3)
    ax.set_title("STL Trend Component", color="white", fontsize=16)
    ax.set_xlabel("Date", color="white", fontweight="bold")
    ax.set_ylabel("Trend (°C)", color=colors["predicted"], fontweight="bold")
    for spine in ["bottom", "left", "top", "right"]:
        ax.spines[spine].set_color("white" if spine in ["bottom","top"] else colors["predicted"])
    ax.tick_params(colors="white")
    plt.tight_layout()
    plt.savefig(os.path.join(modeling_folder, "STL_Trend.png"), dpi=300, facecolor=plt.gcf().get_facecolor())
    plt.close()

    # Seasonal
    plt.figure(figsize=(10, 4), facecolor="#000000")
    ax = plt.gca()
    ax.set_facecolor("#000000")
    ax.plot(ts.index, stl_result.seasonal, color=colors["observed"], lw=3)
    ax.set_title("STL Seasonal Component", color="white", fontsize=16)
    ax.set_xlabel("Date", color="white", fontweight="bold")
    ax.set_ylabel("Seasonal", color=colors["observed"], fontweight="bold")
    for spine in ["bottom", "left", "top", "right"]:
        ax.spines[spine].set_color("white" if spine in ["bottom","top"] else colors["observed"])
    ax.tick_params(colors="white")
    plt.tight_layout()
    plt.savefig(os.path.join(modeling_folder, "STL_Seasonal.png"), dpi=300, facecolor=plt.gcf().get_facecolor())
    plt.close()

    # Residual
    plt.figure(figsize=(10, 4), facecolor="#000000")
    ax = plt.gca()
    ax.set_facecolor("#000000")
    ax.plot(ts.index, stl_result.resid, color="grey", lw=2)
    ax.set_title("STL Residual Component", color="white", fontsize=16)
    ax.set_xlabel("Date", color="white", fontweight="bold")
    ax.set_ylabel("Residual", color="grey", fontweight="bold")
    for spine in ["bottom", "left", "top", "right"]:
        ax.spines[spine].set_color("white")
    ax.tick_params(colors="white")
    plt.tight_layout()
    plt.savefig(os.path.join(modeling_folder, "STL_Residuals.png"), dpi=300, facecolor=plt.gcf().get_facecolor())
    plt.close()

except Exception as e:
    print(f"Error during STL decomposition or plotting: {e}")

print("🔥 Relationship and modeling analysis done. Outputs saved in:")
print(f" - Relationship analysis folder: {relationship_folder}")
print(f" - Modeling analysis folder: {modeling_folder}")
