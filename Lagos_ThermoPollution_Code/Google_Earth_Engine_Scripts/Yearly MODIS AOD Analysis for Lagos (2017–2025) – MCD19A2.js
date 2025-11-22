// Load Lagos boundary from your asset
var lagos = ee.FeatureCollection('projects/golden-cosmos-397908/assets/Lagos');

// Define years of interest
var startYear = 2017;
var endYear = 2025;
var years = ee.List.sequence(startYear, endYear);

// Load MODIS AOD dataset
var aodCollection = ee.ImageCollection('MODIS/061/MCD19A2_GRANULES')
                      .select('Optical_Depth_047');

// Function to calculate yearly mean AOD
var yearlyAOD = years.map(function(year) {
  year = ee.Number(year);
  var start = ee.Date.fromYMD(year, 1, 1);
  var end = start.advance(1, 'year');

  var filtered = aodCollection.filterDate(start, end);

  var meanImage = ee.Image(ee.Algorithms.If(
    filtered.size().gt(0),
    filtered.mean(),
    ee.Image.constant(-9999).rename('AOD')
  ));

  var stats = meanImage.reduceRegion({
    reducer: ee.Reducer.mean(),
    geometry: lagos.geometry(),
    scale: 1000,
    maxPixels: 1e13
  });

  var value = ee.Algorithms.If(
    stats.size().gt(0),
    ee.Number(stats.get('Optical_Depth_047')),
    -9999
  );

  return ee.Feature(null, {
    'Year': year,
    'Mean_AOD': value
  });
});

// Convert to FeatureCollection
var yearlyAODCollection = ee.FeatureCollection(yearlyAOD);

// Print sample
print('Yearly AOD for Lagos (2017–2025):', yearlyAODCollection.limit(10));

// Export to CSV
Export.table.toDrive({
  collection: yearlyAODCollection,
  description: 'Lagos_Yearly_AOD_2017_2025',
  fileFormat: 'CSV',
  folder: 'Lagos_AOD_Results'
}); 
