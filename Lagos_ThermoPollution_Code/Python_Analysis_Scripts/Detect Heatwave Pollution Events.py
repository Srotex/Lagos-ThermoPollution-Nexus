import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# === Folder paths ===
data_folder = r"C:\Users\clemo\Desktop\School\Article\Quantifying the Thermo Pollution Coupling LST AOD Dynamics in Lagos Metropolitan Area Nigeria\DATA"
climate_folder = os.path.join(data_folder, "climate")
event_folder = os.path.join(climate_folder, "event_detection")
os.makedirs(event_folder, exist_ok=True)  # Create event_detection folder if not exists

# === Files ===
files = {
    "monthly_aod": "Lagos_Monthly_AOD_2017_2025.csv",
    "monthly_lst": "Lagos_Monthly_LST_2017_2025.csv"
}

# === Load Data with error handling ===
try:
    df_aod = pd.read_csv(os.path.join(data_folder, files['monthly_aod']))
    df_lst = pd.read_csv(os.path.join(data_folder, files['monthly_lst']))
except Exception as e:
    raise RuntimeError(f"Error loading data files: {e}")

# === Construct Date from Year & Month ===
df_aod['Date'] = pd.to_datetime(dict(year=df_aod['Year'], month=df_aod['Month'], day=1))
df_lst['Date'] = pd.to_datetime(dict(year=df_lst['Year'], month=df_lst['Month'], day=1))

# === Select only necessary columns and rename for merge ===
df_aod = df_aod[['Date', 'Mean_AOD']]
df_lst = df_lst[['Date', 'Mean_LST_Celsius']]

# === Merge on Date ===
df = pd.merge(df_lst, df_aod, on='Date')
df.set_index('Date', inplace=True)
df = df.sort_index()

print("Data covers from:", df.index.min(), "to", df.index.max())
print("Sample dates:", df.index[:5])

# === Calculate anomalies and z-scores ===
df['LST_anom'] = df['Mean_LST_Celsius'] - df['Mean_LST_Celsius'].mean()
df['AOD_anom'] = df['Mean_AOD'] - df['Mean_AOD'].mean()

df['LST_anom_z'] = (df['LST_anom'] - df['LST_anom'].mean()) / df['LST_anom'].std()
df['AOD_anom_z'] = (df['AOD_anom'] - df['AOD_anom'].mean()) / df['AOD_anom'].std()

# === Event Detection Function with min_duration_months parameter ===
def detect_events(series, time_index, method='percentile', pct=90, z_thresh=1.5, min_duration_months=2):
    if method == 'percentile':
        threshold = np.percentile(series, pct)
        mask = series > threshold
    elif method == 'zscore':
        mask = series > z_thresh
    else:
        raise ValueError("Method must be 'percentile' or 'zscore'.")

    events = []
    in_event = False
    start_date = None

    for idx, val in enumerate(mask):
        if val and not in_event:
            in_event = True
            start_date = time_index[idx]
        elif not val and in_event:
            end_date = time_index[idx - 1]
            duration = (end_date.to_period('M') - start_date.to_period('M')).n + 1
            if duration >= min_duration_months:
                events.append((start_date, end_date, duration))
            in_event = False

    # If still in event at the end
    if in_event:
        end_date = time_index[-1]
        duration = (end_date.to_period('M') - start_date.to_period('M')).n + 1
        if duration >= min_duration_months:
            events.append((start_date, end_date, duration))

    return events, mask

# === Detect events with updated min_duration_months=2 ===
LST_pct = 90
AOD_pct = 90
LST_z = 1.5
AOD_z = 1.5
min_dur = 2

lst_events_pct, lst_mask_pct = detect_events(df['LST_anom'].values, df.index, method='percentile', pct=LST_pct, min_duration_months=min_dur)
lst_events_z, lst_mask_z = detect_events(df['LST_anom_z'].values, df.index, method='zscore', z_thresh=LST_z, min_duration_months=min_dur)

aod_events_pct, aod_mask_pct = detect_events(df['AOD_anom'].values, df.index, method='percentile', pct=AOD_pct, min_duration_months=min_dur)
aod_events_z, aod_mask_z = detect_events(df['AOD_anom_z'].values, df.index, method='zscore', z_thresh=AOD_z, min_duration_months=min_dur)

# === Print event summaries ===
def print_events(events, event_name):
    print(f"\n{event_name} events detected: {len(events)}")
    for i, (start, end, dur) in enumerate(events, 1):
        print(f"  Event {i}: {start.strftime('%Y-%m')} to {end.strftime('%Y-%m')} (Duration: {dur} months)")

print_events(lst_events_pct, "Heatwave (LST) by Percentile")
print_events(lst_events_z, "Heatwave (LST) by Z-score")
print_events(aod_events_pct, "High Pollution (AOD) by Percentile")
print_events(aod_events_z, "High Pollution (AOD) by Z-score")

# === Plot side-by-side anomalies with event masks ===
fig, ax = plt.subplots(2, 1, figsize=(14, 8), sharex=True, facecolor="#000000")

# Updated print-friendly colors
lst_color = "#d62728"  # red
aod_color = "#9467bd"  # purple

ax[0].plot(df.index, df['LST_anom'], label='LST Anomaly', color=lst_color)
ax[0].fill_between(df.index, df['LST_anom'], where=lst_mask_pct, color=lst_color, alpha=0.3, label='Heatwave Event')
ax[0].axhline(0, color='white', linewidth=0.8)
ax[0].set_ylabel("LST Anomaly")
ax[0].legend(facecolor="#000000", framealpha=0.5)
ax[0].set_title("Heatwave Detection in Lagos")

ax[1].plot(df.index, df['AOD_anom'], label='AOD Anomaly', color=aod_color)
ax[1].fill_between(df.index, df['AOD_anom'], where=aod_mask_pct, color=aod_color, alpha=0.3, label='High Pollution Event')
ax[1].axhline(0, color='white', linewidth=0.8)
ax[1].set_ylabel("AOD Anomaly")
ax[1].legend(facecolor="#000000", framealpha=0.5)
ax[1].set_title("High Pollution Detection in Lagos")

for a in ax:
    a.tick_params(colors='white')
    for spine in a.spines.values():
        spine.set_color('white')

plt.tight_layout()

fig_path = os.path.join(event_folder, "anomaly_heatwave_pollution.png")
try:
    fig.savefig(fig_path, dpi=300, facecolor=fig.get_facecolor())
    print(f"\nSaved anomaly figure to {fig_path}")
except Exception as e:
    print(f"Warning: Could not save anomaly figure: {e}")
plt.show()

# === Heatmap Calendar Visualization Function ===
def create_event_heatmap(mask, dates, title, cmap, filename):
    df_events = pd.DataFrame({'Event': mask}, index=dates)
    df_events['Year'] = df_events.index.year
    df_events['Month'] = df_events.index.month

    heatmap_data = df_events.pivot_table(index='Year', columns='Month', values='Event', aggfunc='sum', fill_value=0)

    # Ensure all months present 1-12
    for m in range(1, 13):
        if m not in heatmap_data.columns:
            heatmap_data[m] = 0
    heatmap_data = heatmap_data[sorted(heatmap_data.columns)]

    fig, ax = plt.subplots(figsize=(12, 6), facecolor="#000000")
    sns.heatmap(heatmap_data, cmap=cmap, cbar=True, linewidths=0.5,
                linecolor='gray', square=True, ax=ax)

    ax.set_title(title, color='white', fontsize=16, fontweight='bold')
    ax.set_xlabel("Month", color='white', fontsize=14)
    ax.set_ylabel("Year", color='white', fontsize=14)

    ax.tick_params(colors='white', rotation=0)
    ax.set_xticks(np.arange(0.5, 12.5, 1))
    # If you want real season labels, replace the list below with ['Dry', 'Wet', ...] accordingly
    ax.set_xticklabels(['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                        'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'], color='white')
    ax.yaxis.set_ticklabels(ax.get_yticklabels(), color='white')

    plt.tight_layout()
    heatmap_path = os.path.join(event_folder, filename)
    try:
        fig.savefig(heatmap_path, dpi=300, facecolor=fig.get_facecolor())
        print(f"Saved heatmap figure to {heatmap_path}")
    except Exception as e:
        print(f"Warning: Could not save heatmap figure: {e}")
    plt.show()

# === Generate heatmaps ===
create_event_heatmap(lst_mask_pct, df.index, "Heatwave Events Calendar (Percentile Threshold)", "Reds", "heatwave_events_calendar.png")
create_event_heatmap(aod_mask_pct, df.index, "High Pollution Events Calendar (Percentile Threshold)", "Purples", "pollution_events_calendar.png")

# === Composite plot for Z-score anomalies (from script 6 merged here) ===
plt.figure(figsize=(14, 6), facecolor="#000000")
plt.plot(df.index, df['LST_anom_z'], label='LST Anomaly Z-score', color=lst_color, linewidth=2)
plt.plot(df.index, df['AOD_anom_z'], label='AOD Anomaly Z-score', color=aod_color, linewidth=2)
plt.axhline(0, color='white', linestyle='--', linewidth=1)

plt.fill_between(df.index, 0, df['LST_anom_z'], where=df['LST_anom_z'] > 1.5, color=lst_color, alpha=0.2, label='LST High Anomaly')
plt.fill_between(df.index, 0, df['AOD_anom_z'], where=df['AOD_anom_z'] > 1.5, color=aod_color, alpha=0.2, label='AOD High Anomaly')

plt.title("Composite Z-score Anomalies for LST & AOD", color='white', fontsize=16)
plt.ylabel("Z-score Anomaly", color='white', fontsize=14)
plt.xlabel("Date", color='white', fontsize=14)

plt.legend(facecolor="#000000")
plt.grid(alpha=0.3, linestyle='--')
plt.tick_params(colors='white')

plt.tight_layout()
composite_path = os.path.join(event_folder, "zscore_composite_anomalies.png")
try:
    plt.savefig(composite_path, dpi=300, facecolor=plt.gcf().get_facecolor())
    print(f"Saved composite anomalies plot to {composite_path}")
except Exception as e:
    print(f"Warning: Could not save composite anomalies plot: {e}")
plt.show()
