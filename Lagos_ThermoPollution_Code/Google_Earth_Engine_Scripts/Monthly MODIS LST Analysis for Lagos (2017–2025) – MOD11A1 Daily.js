// Load Lagos boundary from your asset
var lagos = ee.FeatureCollection('projects/golden-cosmos-397908/assets/Lagos');

// Define time range
var startYear = 2017;
var endYear = 2025;
var years = ee.List.sequence(startYear, endYear);
var months = ee.List.sequence(1, 12);

// Load MODIS LST Collection
var lst = ee.ImageCollection('MODIS/061/MOD11A1')
            .select('LST_Day_1km');

// Convert Kelvin to Celsius, clip to Lagos, and retain properties
var lstCelsius = lst.map(function(image) {
  var processed = image
    .multiply(0.02)
    .subtract(273.15)
    .rename('LST_Celsius')
    .clip(lagos);
    
  return processed.copyProperties(image, image.propertyNames());
});

// Main loop: calculate monthly means
var monthlyStats = years.map(function(y) {
  return months.map(function(m) {
    var start = ee.Date.fromYMD(y, m, 1);
    var end = start.advance(1, 'month');

    var filtered = lstCelsius.filterDate(start, end);

    var meanImage = ee.Image(ee.Algorithms.If(
      filtered.size().gt(0),
      filtered.mean(),
      ee.Image.constant(-9999).rename('LST_Celsius')
    ));

    var stats = meanImage.reduceRegion({
      reducer: ee.Reducer.mean(),
      geometry: lagos.geometry(),
      scale: 1000,
      maxPixels: 1e13
    });

    var value = ee.Algorithms.If(
      stats.size().gt(0),
      ee.Number(stats.get('LST_Celsius')),
      -9999
    );

    return ee.Feature(null, {
      'Year': y,
      'Month': m,
      'Mean_LST_Celsius': value
    });
  });
}).flatten();

// Convert to FeatureCollection
var monthlyCollection = ee.FeatureCollection(monthlyStats);

// Print first few results to console
print('Monthly LST for Lagos (2017–2025):', monthlyCollection.limit(10));

// Export to Google Drive as CSV
Export.table.toDrive({
  collection: monthlyCollection,
  description: 'Lagos_Monthly_LST_2017_2025',
  fileFormat: 'CSV',
  folder: 'Lagos_LST_Results'
});
