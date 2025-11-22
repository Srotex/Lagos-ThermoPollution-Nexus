// Load Lagos boundary
var lagos = ee.FeatureCollection('projects/golden-cosmos-397908/assets/Lagos');

// Load MODIS LST (MOD11A1.061) Daily
var modisLST = ee.ImageCollection('MODIS/061/MOD11A1')
                .filterDate('2017-01-01', '2025-12-31')
                .filterBounds(lagos);

// Convert to Celsius and filter good quality data
var lstCelsius = modisLST.map(function(img) {
  var lst = img.select('LST_Day_1km')
               .multiply(0.02)
               .subtract(273.15)
               .rename('LST_Celsius');
  return lst.copyProperties(img, ['system:time_start']);
});

// Function to calculate yearly mean LST
var years = ee.List.sequence(2017, 2025);

var yearlyStats = ee.FeatureCollection(years.map(function(year) {
  year = ee.Number(year);
  var start = ee.Date.fromYMD(year, 1, 1);
  var end = start.advance(1, 'year');
  
  var yearImg = lstCelsius.filterDate(start, end).mean();

  var stats = yearImg.reduceRegion({
    reducer: ee.Reducer.mean(),
    geometry: lagos.geometry(),
    scale: 1000,
    maxPixels: 1e13
  });

  return ee.Feature(null, {
    'Year': year,
    'Mean_LST_Celsius': stats.get('LST_Celsius')
  });
}));

// Print to Console
print('Yearly Mean LST (°C):', yearlyStats);

// Export to Google Drive as CSV
Export.table.toDrive({
  collection: yearlyStats,
  description: 'Lagos_Yearly_LST_2017_2025',
  fileFormat: 'CSV',
  folder: 'Lagos_LST_Results'
}); 
