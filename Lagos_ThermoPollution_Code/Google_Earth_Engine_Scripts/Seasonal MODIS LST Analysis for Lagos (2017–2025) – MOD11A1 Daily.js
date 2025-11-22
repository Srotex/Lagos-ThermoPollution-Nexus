// Load Lagos boundary from your asset
var lagos = ee.FeatureCollection('projects/golden-cosmos-397908/assets/Lagos');

// Define time range
var startYear = 2017;
var endYear = 2025;
var years = ee.List.sequence(startYear, endYear);

// Load MODIS LST Collection (LST Day 1km band)
var lst = ee.ImageCollection('MODIS/061/MOD11A1')
            .select('LST_Day_1km');

// Convert to Celsius, clip to Lagos, and retain properties
var lstCelsius = lst.map(function(image) {
  var processed = image
    .multiply(0.02)
    .subtract(273.15)
    .rename('LST_Celsius')
    .clip(lagos);
    
  return processed.copyProperties(image, image.propertyNames());
});


// Define seasons with start and end months
var seasons = ee.List([
  {'name': 'Dry_Season', 'startMonth': 11, 'endMonth': 3},
  {'name': 'Wet_Season', 'startMonth': 4, 'endMonth': 10}
]);

// Loop through each year and season
var seasonalStats = years.map(function(y) {
  var year = ee.Number(y);

  return ee.List(seasons.map(function(s) {
    var season = ee.Dictionary(s);
    var name = season.get('name');
    var startMonth = ee.Number(season.get('startMonth'));
    var endMonth = ee.Number(season.get('endMonth'));

    var filtered;
    if (startMonth.gt(endMonth)) {
      // Dry season spans two years (Nov–Mar)
      var part1 = lstCelsius.filterDate(
        ee.Date.fromYMD(year, startMonth, 1),
        ee.Date.fromYMD(year, 12, 31).advance(1, 'day')
      );
      var part2 = lstCelsius.filterDate(
        ee.Date.fromYMD(year.add(1), 1, 1),
        ee.Date.fromYMD(year.add(1), endMonth, 1).advance(1, 'month')
      );
      filtered = part1.merge(part2);
    } else {
      // Wet season is within same year (Apr–Oct)
      filtered = lstCelsius.filterDate(
        ee.Date.fromYMD(year, startMonth, 1),
        ee.Date.fromYMD(year, endMonth, 1).advance(1, 'month')
      );
    }

    // Calculate mean LST image
    var mean = ee.Image(ee.Algorithms.If(
      filtered.size().gt(0),
      filtered.mean(),
      ee.Image.constant(-9999).rename('LST_Celsius')
    ));

    // Reduce to region mean
    var stats = mean.reduceRegion({
      reducer: ee.Reducer.mean(),
      geometry: lagos.geometry(),
      scale: 1000,
      maxPixels: 1e13
    });

    // Extract result safely
    var value = ee.Algorithms.If(
      stats.size().gt(0),
      ee.Number(stats.get('LST_Celsius')),
      -9999
    );

    // Return a feature with Year, Season, and LST value
    return ee.Feature(null, {
      'Year': year,
      'Season': name,
      'Mean_LST_Celsius': value
    });
  }));
}).flatten();

// Convert list to FeatureCollection
var finalCollection = ee.FeatureCollection(seasonalStats);

// Print sample to console
print('Seasonal LST for Lagos (2017–2025):', finalCollection.limit(10));

// Export result as CSV to Google Drive
Export.table.toDrive({
  collection: finalCollection,
  description: 'Lagos_Seasonal_LST_2017_2025',
  fileFormat: 'CSV',
  folder: 'Lagos_LST_Results'  // ensure this folder exists or it will go to root
});
