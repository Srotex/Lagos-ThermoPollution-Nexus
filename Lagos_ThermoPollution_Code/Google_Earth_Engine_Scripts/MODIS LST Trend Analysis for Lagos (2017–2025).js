// =======================================
// 1. Import Lagos Asset
// =======================================
var lagos = ee.FeatureCollection('projects/golden-cosmos-397908/assets/Lagos');

// =======================================
// 2. Load MODIS Terra LST (MOD11A2 - 8-day, 1km)
// =======================================
var modis = ee.ImageCollection('MODIS/006/MOD11A2')
              .filterBounds(lagos)
              .filterDate('2017-01-01', '2025-12-31')
              .select('LST_Day_1km');

// =======================================
// 3. Convert LST from Kelvin to Celsius
// =======================================
var modis_celsius = modis.map(function(img) {
  return img
    .multiply(0.02)
    .subtract(273.15)
    .copyProperties(img, ['system:time_start']);
});

// =======================================
// 4. Create Annual Mean LST Images
// =======================================
var years = ee.List.sequence(2017, 2025);

var annualImages = ee.ImageCollection(
  years.map(function(y) {
    var year = ee.Number(y).toInt();
    var yearLST = modis_celsius
      .filter(ee.Filter.calendarRange(year, year, 'year'))
      .mean()
      .set('year', year)
      .set('system:time_start', ee.Date.fromYMD(year, 6, 1));
      
    return yearLST;
  })
);

// =======================================
// 5. Stack Annual Images into Multi-band Image for Trend Analysis
// =======================================
var withYearBand = annualImages.map(function(image) {
  var year = ee.Number(image.get('year'));
  return image.addBands(ee.Image.constant(year).rename('year').toFloat());
});

// =======================================
// 6. Apply Linear Regression (LST vs Year)
// =======================================
var trend = withYearBand.reduce(ee.Reducer.linearFit());

// Extract the slope band
var slope = trend.select('scale');

// =======================================
// 7. Visualization Parameters
// =======================================
var visParams = {
  min: -0.2,
  max: 0.2,
  palette: ['blue', 'white', 'red']
};

// =======================================
// 8. Display Map
// =======================================
Map.centerObject(lagos, 9);
Map.addLayer(slope.clip(lagos), visParams, 'LST Trend (°C/year)');
Map.addLayer(lagos.style({color: 'black', fillColor: '00000000'}), {}, 'Lagos Boundary');

// =======================================
// 9. Optional: Print Statistics
// =======================================
print('LST Trend Image (slope °C/year)', slope);


// =======================================
// 10. Export slope image to Google Drive
// =======================================
Export.image.toDrive({
  image: slope.clip(lagos),
  description: 'LST_Trend_Lagos_2017_2025',
  folder: 'EarthEngine_Exports',  // Change to your preferred Drive folder
  fileNamePrefix: 'LST_Trend_Lagos_2017_2025',
  region: lagos.geometry(),
  scale: 1000,  // MODIS native resolution
  crs: 'EPSG:4326',
  maxPixels: 1e13
});
