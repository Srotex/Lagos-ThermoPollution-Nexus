import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from scipy.stats import linregress
import pymannkendall as mk

# Setup
sns.set_theme(style="darkgrid")
plt.rcParams.update({
    "font.size": 13,
    "axes.titlesize": 16,
    "axes.labelsize": 14,
    "legend.fontsize": 12,
    "xtick.labelsize": 11,
    "ytick.labelsize": 11,
    "axes.linewidth": 1.2,
    "lines.linewidth": 2.5,
    "figure.facecolor": "#000000",
    "axes.facecolor": "#000000",
    "savefig.facecolor": "#000000",
    "axes.edgecolor": "white",
    "xtick.color": "white",
    "ytick.color": "white",
    "text.color": "white"
})

# Folder setup
data_folder = r"C:\Users\clemo\Desktop\School\Article\Quantifying the Thermo Pollution Coupling LST AOD Dynamics in Lagos Metropolitan Area Nigeria\DATA"
output_folder = os.path.join(data_folder, "trend_analysis")
os.makedirs(output_folder, exist_ok=True)

# Load and prepare data
def load_and_prepare_data():
    """Load monthly AOD and LST data and create datetime index"""
    try:
        monthly_aod = pd.read_csv(os.path.join(data_folder, "Lagos_Monthly_AOD_2017_2025.csv"))
        monthly_lst = pd.read_csv(os.path.join(data_folder, "Lagos_Monthly_LST_2017_2025.csv"))
        
        # Merge datasets
        monthly = pd.merge(monthly_aod, monthly_lst, on=["Year", "Month"])
        monthly['Date'] = pd.to_datetime(monthly[['Year', 'Month']].assign(DAY=1))
        monthly = monthly.sort_values('Date')
        monthly = monthly.dropna(subset=['Mean_AOD', 'Mean_LST_Celsius'])
        
        return monthly
    except Exception as e:
        print(f"Error loading data: {e}")
        return None

def calculate_trend_statistics(series, dates, variable_name):
    """Calculate trend statistics including Mann-Kendall test and Sen's slope"""
    # Mann-Kendall test
    mk_result = mk.original_test(series)
    
    # Linear regression for trend line
    x = np.arange(len(series))
    slope, intercept, r_value, p_value, std_err = linregress(x, series)
    
    # Sen's slope
    sen_slope = mk.sens_slope(series).slope
    
    # Annual change (assuming monthly data)
    annual_change = sen_slope * 12
    
    return {
        'variable': variable_name,
        'trend': mk_result.trend,
        'p_value': mk_result.p,
        'sen_slope': sen_slope,
        'annual_change': annual_change,
        'slope': slope,
        'intercept': intercept,
        'r_squared': r_value**2,
        'z_statistic': mk_result.z if hasattr(mk_result, 'z') else None
    }

def create_trend_figure(data, variable, title, filename, color, legend_loc):
    """Create clean trend figure without statistics table"""
    fig, ax = plt.subplots(figsize=(12, 6), facecolor="#000000")
    
    # Plot original data
    ax.plot(data['Date'], data[variable], 
            color=color, linewidth=2, marker='o', markersize=3,
            label=f'Monthly {title.split("(")[0].strip()}', alpha=0.7)
    
    # Calculate and plot trend line
    x_numeric = np.arange(len(data))
    slope, intercept, _, _, _ = linregress(x_numeric, data[variable])
    trend_line = intercept + slope * x_numeric
    
    ax.plot(data['Date'], trend_line, 
            color='red', linewidth=3, linestyle='--',
            label='Linear Trend')
    
    # Calculate statistics (for CSV export only, not displayed)
    stats = calculate_trend_statistics(data[variable], data['Date'], title)
    
    # Styling - Clean without statistics box
    ax.set_title(f'Figure: Trend of {title} in the Study Area', 
                 color='white', fontweight='bold', pad=20)
    ax.set_xlabel('Date', color='white', fontweight='bold')
    
    if 'AOD' in title:
        ax.set_ylabel('Aerosol Optical Depth (AOD)', color='white', fontweight='bold')
    else:
        ax.set_ylabel('Land Surface Temperature (°C)', color='white', fontweight='bold')
    
    # Position legend based on parameter
    ax.legend(facecolor='#000000', edgecolor='white', 
              loc=legend_loc, framealpha=0.9)
    
    # Grid and spines
    ax.grid(True, alpha=0.3, linestyle='--')
    for spine in ax.spines.values():
        spine.set_color('white')
    
    ax.tick_params(colors='white')
    
    plt.tight_layout()
    
    # Save figure
    save_path = os.path.join(output_folder, filename)
    plt.savefig(save_path, dpi=300, bbox_inches='tight', 
                facecolor=fig.get_facecolor())
    plt.close()
    
    return stats

def main():
    """Main function to generate clean trend figures"""
    print("Loading data...")
    data = load_and_prepare_data()
    
    if data is None:
        print("Failed to load data. Exiting.")
        return
    
    print(f"Data loaded: {len(data)} monthly records from {data['Date'].min()} to {data['Date'].max()}")
    
    # Colors for plots
    colors = {
        'AOD': '#1f77b4',  # Blue
        'LST': '#ff7f0e'   # Orange
    }
    
    # Create Figure 3: AOD Trend - Legend in top right
    print("Creating Figure 3: AOD Trend...")
    aod_stats = create_trend_figure(
        data, 
        'Mean_AOD', 
        'Aerosol Optical Depth (AOD)', 
        'Figure3_AOD_Trend.png', 
        colors['AOD'],
        legend_loc='upper right'      # Legend top right corner
    )
    
    # Create Figure 4: LST Trend - Legend in bottom left  
    print("Creating Figure 4: LST Trend...")
    lst_stats = create_trend_figure(
        data, 
        'Mean_LST_Celsius', 
        'Land Surface Temperature (LST)', 
        'Figure4_LST_Trend.png', 
        colors['LST'],
        legend_loc='lower left'       # Legend bottom left corner
    )
    
    # Save trend statistics to CSV (for reference, not displayed on plots)
    stats_df = pd.DataFrame([aod_stats, lst_stats])
    stats_path = os.path.join(output_folder, 'trend_statistics.csv')
    stats_df.to_csv(stats_path, index=False)
    
    print(f"\n✅ Clean trend analysis complete!")
    print(f"📊 Figures saved in: {output_folder}")
    print(f"📈 AOD Trend: {aod_stats['trend']} (p={aod_stats['p_value']:.4f})")
    print(f"🌡️  LST Trend: {lst_stats['trend']} (p={lst_stats['p_value']:.4f})")
    print(f"📋 Statistics saved to: {stats_path}")
    
    return stats_df

# Run the analysis
if __name__ == "__main__":
    trend_stats = main()