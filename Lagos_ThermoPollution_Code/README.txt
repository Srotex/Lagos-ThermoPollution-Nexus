LAGOS THERMO-POLLUTION NEXUS ANALYSIS (2017-2025)
==================================================

This repository contains code for the study "Unmasking the Thermo-Pollution Nexus: A Multi-Modal Decomposition of LST-AOD Dynamics in a Tropical Megacity"

FOLDER STRUCTURE:
├── README.txt (this file)
├── Google_Earth_Engine_Scripts/ (MODIS data processing)
│   ├── Lagos_AOD_Trend_Analysis_2017-2025.js
│   ├── Lagos_Annual_AOD_Statistics_2017-2025.js
│   ├── Lagos_Seasonal_AOD_Statistics_2017-2025.js
│   └── Lagos_Monthly_AOD_Statistics_2017-2025.js
└── Python_Analysis_Scripts/ (Statistical analysis & modeling)
    ├── Lagos_LST_AOD_TimeSeries_Analysis.ipynb
    ├── Lagos_ThermoPollution_Statistical_Models.ipynb
    └── Lagos_Extreme_Event_Detection.ipynb

EXECUTION ORDER:
1. Run GEE scripts in Google Earth Engine to extract AOD data
2. Use Python scripts for statistical analysis and modeling

PREREQUISITES:
- Google Earth Engine account
- Python 3.8+ with pandas, numpy, scipy, pymannkendall, statsmodels, scikit-learn

DATA SOURCES:
- MODIS Terra MOD11A1.061 (LST)
- MODIS MCD19A2.061 (AOD)
- Processed via Google Earth Engine

CONTACT:
Jibril Olarotimi Salawu - Salawurotimi@gmail.com