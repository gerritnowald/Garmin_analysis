import gpxpy
import pandas
import datetime
import numpy as np
from scipy.optimize import minimize_scalar

def gpx2df(file):
    """ parses .gpx file to pandas dataframe """
    # read file
    with open(file, 'r') as gpx_file:
        gpx = gpxpy.parse(gpx_file)

    # absolute time --> activity time
    start = gpx.get_time_bounds()[0]
    gpx.adjust_time(- datetime.timedelta(hours=start.hour, minutes=start.minute, seconds=start.second))

    # calculate distance & speed
    segment = gpx.tracks[0].segments[0]
    for ind, point in enumerate(segment.points):
        point.distance = gpx.get_points_data()[ind][1]
        point.speed    = segment.get_speed(ind)

    # create dataframe (using dictionaries)
    time = []
    data = []
    for point in gpx.tracks[0].segments[0].points:
        time.append(point.time.time())  # removes time zone and day
        data_point = {
            'distance / m'  : point.distance,
            'latitude / °'  : point.latitude,
            'longitude / °' : point.longitude,
            'elevation / m' : point.elevation,
            'speed / km/h'  : point.speed * 3.6,
            # https://stackoverflow.com/questions/48795435/gpxpy-how-to-extract-heart-rate-data-from-gpx-file
            'heart rate / bpm' : int(point.extensions[0].find('{http://www.garmin.com/xmlschemas/TrackPointExtension/v1}hr').text),
        }
        if (acttype := gpx.tracks[0].type) == 'running':
            data_point['pace / min/km'] = 60 / (point.speed * 3.6)
            if data_point['pace / min/km'] > 10:
                data_point['pace / min/km'] = np.nan
            data_point['cadence / spm'] = 2 * int(point.extensions[0].find('{http://www.garmin.com/xmlschemas/TrackPointExtension/v1}cad').text)
            if data_point['cadence / spm'] == 0:
                data_point['cadence / spm'] = np.nan
        data.append(data_point)
    df = pandas.DataFrame(data, index = time)

    # calculate slope
    df['slope / %'] = df['elevation / m'].diff() / df['distance / m'].diff() * 100
    df['slope / %'] = df['slope / %'].rolling(2).mean().shift(-1)

    return df, acttype


def getstats(dataframes,files,acttype):
    """ calculates overall statistics from dataframe """
    data = []
    for df in dataframes:
        stats = {
            'time'         : df.index.values[-1],
            'distance / m' : round(df["distance / m"].iloc[-1])
        }
        if acttype == 'running':
            avg_pace = pandas.to_timedelta(df['pace / min/km'], unit='m').mean()
            stats['avg pace / min/km'] = str(avg_pace).split()[2][3:11]
        else:
            stats['avg spd / km/h'] = round(df["speed / km/h"].mean(),1)
            stats['max spd / km/h'] = round(df["speed / km/h"].max() ,1)
        stats['avg HR / bpm'] = round(df["heart rate / bpm"].mean())
        stats['max HR / bpm'] =       df["heart rate / bpm"].max()
        if acttype == 'running':
            stats['cadence / spm'] = round(df["cadence / spm"].mean())
        data.append(stats)
    stats = pandas.DataFrame(data, index = files).transpose()
    return stats


def rmsq(Δl,A,B):
    """ difference between elevation profiles depending on distance offset """
    yBnew = np.interp(A[:,0], B[:,0] + Δl, B[:,1])  # interpolate elevations to compare
    return sum((A[:,1] - yBnew)**2)                 # square sum of error


def find_dist_off(dataframes):
    """ determines distance offset to match elevation profiles """
    Δl = np.zeros(len(dataframes))
    A  = dataframes[0][['distance / m','elevation / m']].to_numpy()
    for ind in range(1,len(dataframes)):    # offsets wrt 1st activity
        B   = dataframes[ind][['distance / m','elevation / m']].to_numpy()
        res = minimize_scalar(rmsq, args=(A,B))
        Δl[ind] = res.x
    return Δl