// -------------------------------
// Seasonal AOD (MCD19A2) for Lagos
// -------------------------------

// 1) Load Lagos boundary (your asset)
var lagos = ee.FeatureCollection('projects/golden-cosmos-397908/assets/Lagos');

// 2) Parameters
var startYear = 2017;
var endYear   = 2025;
var years     = ee.List.sequence(startYear, endYear);

// 3) Load AOD collection and pre-process each image: select band -> rename -> clip -> copyProperties
var aodCollection = ee.ImageCollection('MODIS/061/MCD19A2_GRANULES')
  .filterBounds(lagos)
  .filterDate(ee.Date.fromYMD(startYear, 1, 1), ee.Date.fromYMD(endYear, 12, 31).advance(1, 'day'))
  .map(function(image) {
    var img = image.select('Optical_Depth_047').rename('AOD'); // pick band and rename
    img = img.clip(lagos); // clip the image to the region
    return img.copyProperties(image, ['system:time_start']); // keep time metadata
  });

// 4) Define seasons (startMonth, endMonth). If startMonth > endMonth, season spans two calendar years.
var seasons = ee.List([
  ee.Dictionary({'name': 'Dry_Season', 'startMonth': 11, 'endMonth': 3}), // Nov–Mar
  ee.Dictionary({'name': 'Wet_Season', 'startMonth': 4,  'endMonth': 10}) // Apr–Oct
]);

// 5) Function to compute seasonal mean AOD for a given year
var seasonalForYear = function(year) {
  year = ee.Number(year);

  var feats = seasons.map(function(s) {
    s = ee.Dictionary(s);
    var name = s.get('name');
    var startMonth = ee.Number(s.get('startMonth'));
    var endMonth = ee.Number(s.get('endMonth'));

    // Build seasonal collection (handle cross-year seasons)
    var seasonalCollection = ee.ImageCollection(ee.Algorithms.If(
      startMonth.gt(endMonth),
      // spans two years: part1 = startMonth..Dec of 'year', part2 = Jan..endMonth of 'year+1'
      aodCollection.filterDate(
        ee.Date.fromYMD(year, startMonth, 1),
        ee.Date.fromYMD(year, 12, 31).advance(1, 'day')
      ).merge(
        aodCollection.filterDate(
          ee.Date.fromYMD(year.add(1), 1, 1),
          ee.Date.fromYMD(year.add(1), endMonth, 1).advance(1, 'month')
        )
      ),
      // normal same-year season
      aodCollection.filterDate(
        ee.Date.fromYMD(year, startMonth, 1),
        ee.Date.fromYMD(year, endMonth, 1).advance(1, 'month')
      )
    ));

    // Count images in the seasonal collection
    var count = seasonalCollection.size();

    // Mean image if there are images, else placeholder image with -9999
    var meanImage = ee.Image(ee.Algorithms.If(
      count.gt(0),
      seasonalCollection.mean(),
      ee.Image.constant(-9999).rename('AOD')
    ));

    // Reduce to Lagos mean
    var stats = meanImage.reduceRegion({
      reducer: ee.Reducer.mean(),
      geometry: lagos.geometry(),
      scale: 1000,
      maxPixels: 1e13
    });

    // Safely extract AOD value or -9999
    var value = ee.Algorithms.If(
      count.gt(0),
      ee.Number(ee.Dictionary(stats).get('AOD')),
      -9999
    );

    return ee.Feature(null, {
      'Year': year,
      'Season': name,
      'Mean_AOD': value
    });
  });

  return feats;
};

// 6) Build the flat list of seasonal features across years and convert to FeatureCollection
var seasonalListOfLists = years.map(seasonalForYear); // list of lists
var seasonalFlat = ee.List(seasonalListOfLists).flatten(); // flatten to single list of features
var seasonalFC = ee.FeatureCollection(seasonalFlat);

// 7) Print and export
print('Seasonal AOD for Lagos (2017–2025):', seasonalFC.limit(40));

Export.table.toDrive({
  collection: seasonalFC,
  description: 'Lagos_Seasonal_AOD_2017_2025',
  fileFormat: 'CSV',
  folder: 'Lagos_AOD_Results'   // change if you want a different Drive folder
}); 
