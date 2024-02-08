# compare Garmin activities with gpxpy

Compare arbitrarily many gps-based activities  
- overall stats (time, distance, pace/speed, heart rate, cadence)
- plots over distance: pace/speed, heart rate, cadence, elevation profile
- route on map

GPS-based activities (running, cycling) can be exported as gpx-files from https://connect.garmin.com/.  
This is a general XML-based GPS format which includes  
- coordinates
- elevation
- time

Garmin additionally saves the heart rate (and cadence for running) into the gpx.

The gpx-files are parsed using [gpxpy](https://github.com/tkrajina/gpxpy).  
Methods provided by gpxpy are used to calculate the current speed & distance from start.  
Additionally, pace and slope are calculated.

The data is written into pandas dataframes.

Different activities are synchronized s.t. their elevation profiles match.  
This way, activities on the same route with different starting points (e.g. due to gps inaccuracies) can be compared.

## usage

- put exported gpx files of the same activity type into the folder
- run *compare_activities.ipynb*

## dependencies

- gpxpy
- pandas (includes NumPy and matplotlib)
- scipy
- folium

## acknowledgements

https://betterdatascience.com/data-science-for-cycling-how-to-read-gpx-strava-routes-with-python/