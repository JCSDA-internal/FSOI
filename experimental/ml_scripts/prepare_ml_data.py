# coding: utf-8

import multiprocessing as mp
import xarray as xr
import pandas as pd
import numpy as np
import glob
import time
import re

from itertools import product
from math import trunc


# define a function that import level names from a txt file
def get_levels():
    # set level column names (!! levels are different depending on the files)
    # levels = [round(lev, 3) for lev in bkg.lev.unique()]
    f = open('levels.txt', 'r')
    levels = f.read().split('\n')
    f.close()
    return levels


# define a function that creates lat, lon dicts which for an obs lat or lon
# return the two nearest in bgk
def get_coord_dicts():
    
    # get lat and lon bkg possible values
    lat_bkg = np.arange(-90, 90.5, 0.5)
    lon_bkg = np.arange(-180, 180.0, 0.625) # no 180 lon value in bkg
    
    # get lat and lon obs possible values
    lat_keys = np.arange(-90., 90.01, 0.01)
    lon_keys = np.arange(-180., 180.01, 0.01)
    
    # for each possible obs value get the 2 nearest bkg values
    lat_values = [sorted(lat_bkg, key=lambda x: abs(x - lat))[:2] for lat in lat_keys]
    lon_values = [sorted(lon_bkg, key=lambda x: abs(x - lon))[:2] for lon in lon_keys]
    
    # join keys and values into dict
    lat_dict = dict(zip(np.round(lat_keys, 2), lat_values))
    lon_dict = dict(zip(np.round(lon_keys, 2), lon_values))
    
    return lat_dict, lon_dict


# define a function that loads obs and bkg data into pandas dataframes
def load_data(filepath, date):
    
    obs = pd.read_hdf(filepath).xs(['AMSUA_N18', 4], level=['PLATFORM', 'CHANNEL'])
    obs = obs.reset_index(level=[0, 1])
    obs= obs.drop(['OBTYPE', 'OBERR', 'PRESSURE'], axis=1)
    # fix lon between -180/180 instead of 0/360    
    mask_lon = obs[obs['LONGITUDE'] > 180].index.tolist()
    obs.loc[mask_lon, 'LONGITUDE'] = obs.loc[mask_lon, 'LONGITUDE'] - 360
    
    bkg_path = 'Data/bkg/201412/'
    date = date[:-2] + '_' + date[-2:]
    filename = 'e5130_hyb_01.bkg.eta.' + date + 'z.nc4'
    bkg = xr.open_dataset(bkg_path + filename).to_dataframe()\
            .reset_index(level=[0, 1, 2, 3]).drop('time', axis=1)
    
    # fix bkg zeros lat and lon to 0.0 instead of something like -1.79751e-13
    zero_lat_mask = bkg[(bkg['lat'] < 0.1) & (bkg['lat'] > -0.1)].index.tolist()
    zero_lon_mask = bkg[(bkg['lon'] < 0.1) & (bkg['lon'] > -0.1)].index.tolist()
    
    bkg.loc[zero_lat_mask, 'lat'] = 0.0
    bkg.loc[zero_lon_mask, 'lon'] = 0.0
    
    bkg.set_index(['lat', 'lon'], inplace=True)
        
    return obs, bkg


# define a function that for an obs append a list with the 4 nearest bkg pts
def get_nearest_pts(obs_row, nearest_pts, lat_dict, lon_dict):
    
    lat = np.round(obs_row.LATITUDE, 2)
    lon = np.round(obs_row.LONGITUDE, 2)
    
    row_nearest_pts = [
            (lat_dict[lat][i], lon_dict[lon][j])
            for i, j in product([0, 1], [0, 1])
            ]
        
    nearest_pts.append(row_nearest_pts)


# define a function that gets bkg levels data for a particular point
def get_lev_data(bkg, ix, level_cols):
    return bkg.loc[ix:ix + 71, level_cols[1:]].copy().stack().reset_index(drop=True)


# define a function that adds level data from bkg 3D to 2D by transposing it
def add_lev_data(bkg_3D, bkg_2D, obs, level_cols, levels, i):
    
    lev_data = []
    
    bkg_2D.index.map(
            lambda ix: lev_data.append(get_lev_data(bkg_3D, ix, level_cols))
            )
    
    lev_data = pd.concat(lev_data, axis=1).transpose().reset_index(drop=True)
        
    lev_data.columns = [
            col + '_' + lev
            for lev in levels
            for col in level_cols[1:]
            ]
    
    bkg_2D = pd.concat([bkg_2D.reset_index(drop=True), lev_data], axis=1)
    bkg_2D = bkg_2D.add_prefix('point' + str(i + 1) + '_')
    
    return bkg_2D


# define a function that get bkg nearest data from observations
def get_nearest_bkg(obs, bkg, lat_dict, lon_dict, level_cols, levels):
    
    nearest_pts, nearest_bkg = [], []
    
    obs.apply(lambda row: get_nearest_pts(row, nearest_pts, lat_dict,
                                          lon_dict), axis=1)
    
    pts = [
            [points[i] for points in nearest_pts]
            for i in range(0, len(nearest_pts[0]))
            ]
    
    for i, pts_i in enumerate(pts):
        
        bkg_3D_i = bkg.loc[pts_i].reset_index(level=[0, 1])
        
        mask_2D = np.arange(0, len(bkg_3D_i), 72)
        bkg_2D_i = bkg_3D_i.drop(level_cols, axis=1).loc[mask_2D, :]
        bkg_2D_i = add_lev_data(bkg_3D_i, bkg_2D_i, obs, level_cols, levels, i)
        
        nearest_bkg.append(bkg_2D_i)
        
        # break to get only first point
        break
        
    nearest_bkg = pd.concat(nearest_bkg, axis=1)
    
    return nearest_bkg


# define a function that merges our training data from all files
def merge_train_data(filepaths, i, n, lat_dict, lon_dict, levels):
    
    level_cols = ['lev', 'delp', 'u', 'v', 'tv', 'sphu', 'ozone', 'qitot', 'qltot']
    ml_data = pd.DataFrame()
    
    for j in range(i, len(filepaths), n):
        
        start = time.time()
        
        filepath = filepaths[j]
        date = re.findall('[0-9]+.h5', filepath)[0][:-3]
        obs, bkg = load_data(filepath, date)
        
        nearest_bkg = get_nearest_bkg(obs, bkg, lat_dict, lon_dict, level_cols,
                                      levels)
        
        merge = pd.concat([obs, nearest_bkg], axis=1)
        ml_data = pd.concat([ml_data, merge], axis=0)
        
        end = time.time()
        print('Merge %s obs and bkg done in: %s min and %s sec' % 
              (date, trunc((end - start)/60), round((end - start)%60)))
        
    return ml_data


pstart = time.time()

gmao_path = 'Data/FSOI_data_GMAO_201412/data/GMAO/'
filepaths = sorted(glob.glob(gmao_path + '*.h5'))
lat_dict, lon_dict = get_coord_dicts()
levels = get_levels()

# define how many process we want to run
n = 4
pool = mp.Pool(processes=n)

# run our processes
results = [
        pool.apply_async(merge_train_data, args=(filepaths, i, n, lat_dict,
                                                 lon_dict, levels))
        for i in range(n)
        ]

results = [p.get() for p in results]

# merge our training data
ml_data = pd.concat(results, axis=0)

# save and compress training data in hdf5 format
start = time.time()

saving_path = 'data/'
filename = 'amsua12_n18_ch4_1pt.h5'
ml_data = ml_data.sort_values(['DATETIME', 'LATITUDE', 'LONGITUDE'])\
                 .reset_index(drop=True)
                             
ml_data.to_hdf(saving_path + filename, key='df', complevel=9)

end = time.time()
print('Saved and compressed in: %s min and %s sec' % (trunc((end - start)/60),
                                                      round((end - start)%60)))
    
# display total program time
pend = time.time()
print('Total program took: %s hours and %s min' % (trunc((pend - pstart)/3600),
                                                   round((pend - pstart)%3600/60)))
