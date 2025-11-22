// -------------------------------
// Monthly AOD (MCD19A2) for Lagos
// -------------------------------

// 1) Load Lagos boundary (your asset)
var lagos = ee.FeatureCollection('projects/golden-cosmos-397908/assets/Lagos');

// 2) Parameters
var startYear = 2017;
var endYear = 2025;
var years = ee.List.sequence(startYear, endYear);
var months = ee.List.sequence(1, 12);

// 3) Load MCD19A2 AOD and preprocess each image properly:
//    select band -> scale -> rename -> clip -> copyProperties
var aodCollection = ee.ImageCollection('MODIS/061/MCD19A2_GRANULES')
  .filterBounds(lagos)
  .filterDate(ee.Date.fromYMD(startYear, 1, 1),
              ee.Date.fromYMD(endYear, 12, 31).advance(1, 'day'))
  .map(function(image) {
    // operate on the image, then clip, then copy properties
    var img = image.select('Optical_Depth_047')   // pick 0.47 µm band
                   .multiply(0.001)               // scale factor
                   .rename('AOD');                // rename for consistency
    var clipped = img.clip(lagos);               // clip the ee.Image
    return clipped.copyProperties(image, ['system:time_start']); // preserve time
  });

// 4) Build monthly features: Year, Month, Mean_AOD (or -9999 if no data)
var monthlyFeatures = years.map(function(y) {
  y = ee.Number(y);
  return months.map(function(m) {
    m = ee.Number(m);
    // filter collection for this year and month
    var monthlyCol = aodCollection
      .filter(ee.Filter.calendarRange(y, y, 'year'))
      .filter(ee.Filter.calendarRange(m, m, 'month'));

    var count = monthlyCol.size();

    // create mean image or placeholder image if collection empty
    var meanImg = ee.Image(ee.Algorithms.If(
      count.gt(0),
      monthlyCol.mean(),
      ee.Image.constant(-9999).rename('AOD')
    ));

    // reduce to Lagos mean
    var stats = meanImg.reduceRegion({
      reducer: ee.Reducer.mean(),
      geometry: lagos.geometry(),
      scale: 1000,
      maxPixels: 1e13
    });

    // extract value safely or set -9999
    var value = ee.Algorithms.If(
      count.gt(0),
      ee.Number(ee.Dictionary(stats).get('AOD')),
      -9999
    );

    return ee.Feature(null, {
      'Year': y,
      'Month': m,
      'Mean_AOD': value
    });
  });
}).flatten();

// 5) Convert to FeatureCollection and preview
var monthlyAOD = ee.FeatureCollection(monthlyFeatures);
print('Monthly AOD for Lagos (2017–2025):', monthlyAOD.limit(24));

// 6) Export to Google Drive as CSV
Export.table.toDrive({
  collection: monthlyAOD,
  description: 'Lagos_Monthly_AOD_2017_2025',
  fileFormat: 'CSV',
  folder: 'Lagos_AOD_Results'   // change if you want a different Drive folder
});
