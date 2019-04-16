#!/usr/bin/env python

'''
correlations_binned_map.py - make spatial maps of FSOI binned correlations
'''

import os
import sys
from argparse import ArgumentParser,ArgumentDefaultsHelpFormatter
from matplotlib import pyplot as plt

sys.path.append('../lib')
import lib_mapping as lmapping
import lib_utils as lutils
import lib_obimpact as loi

def read_centers_raw():
    'Read data and return a dictionary of dataframes, one key per center'
    df = {}
    for center in centers:
        fbinned= '%s/work/%s/%s/%s.h5' % (rootdir,center,norm,platform.lower())
        tmp = lutils.readHDF(fbinned,'df')
        tmp = loi.select(tmp,cycles=cycle,obtypes=obtype,channels=channel)
        tmp.reset_index(inplace=True)
        tmp = tmp.groupby(['DATETIME','LONGITUDE','LATITUDE'])[['TotImp']].agg('sum')
        tmp.columns = [center]
        df[center] = tmp
    return df

def read_centers():
    'Read binned data and return a dictionary of dataframes, one key per center'
    df = {}
    for center in centers:
        fbinned = '%s/work/%s/%s/%s.binned.h5' % (rootdir,center,norm,platform.lower())
        tmp = lutils.readHDF(fbinned,'df')
        tmp = loi.select(tmp,cycles=cycle,obtypes=obtype,channels=channel)
        tmp.reset_index(inplace=True)
        tmp = tmp.groupby(['DATETIME','LONGITUDE','LATITUDE'])[['TotImp']].agg('sum')
        tmp.columns = [center]
        df[center] = tmp
    return df

def compute_std_corr(df):
    'Compute the standard deviation and correlation from dictionary of dataframe'
    stdv = {} ; corr = {}
    for center in centers:

        stdv[center] = df[center].std(level=['LATITUDE','LONGITUDE'])

        if center != ref_center:
            r1 = df[ref_center].join(df[center],lsuffix=ref_center,rsuffix=center)
            r2 = r1.groupby(level=['LATITUDE','LONGITUDE'])
            r3 = r2.corr()[::2][center].reset_index()
            r3.drop('level_2',axis=1,inplace=True)
            corr[center] = r3.set_index(['LATITUDE','LONGITUDE'])

    df_stdv = stdv[ref_center]
    df_corr = corr[center] / corr[center] ; df_corr.columns = [ref_center]
    for center in centers[1:]:
        df_stdv = df_stdv.join(stdv[center])
        df_corr = df_corr.join(corr[center])

    return df_stdv,df_corr

def plot_corr(center,corr,titlestr):

    vmax = 0.6
    vmin = -vmax

    fig = plt.figure()
    lmapping.drawMap(bmap,proj,fillcontinents=False)
    sc = bmap.scatter(xg,yg,c=corr,s=20,marker='s',cmap=cmap,alpha=0.8,edgecolors='face',vmin=vmin,vmax=vmax)
    bmap.colorbar(sc,'right',size='5%',pad='2%')
    plt.title('%s' % (titlestr),fontsize=18)

    if savefig:
        fname = 'Corr-%s-%s-%s' % (ref_center,center,platform)
        if channel is not None:
            fname = '%s-ch%d' % (fname,channel[0])
        lutils.savefigure(fname=fname,fh=fig,format='pdf')

    return

global rootdir,centers,cycle,platform,obtype,channel,norm,savefig
global ref_center,cyclestr
global cmap,proj,bmap,xg,yg

parser = ArgumentParser(description = 'Create and Plot Observation Impact Correlation Maps',formatter_class=ArgumentDefaultsHelpFormatter)
parser.add_argument('--rootdir',help='root path to directory',type=str,default='/scratch3/NCEPDEV/stmp2/Rahul.Mahajan/test/Thomas.Auligne/FSOI',required=False)
parser.add_argument('--norm',help='metric norm',type=str,default='dry',choices=['dry','moist'],required=False)
parser.add_argument('--centers',help='originating centers',nargs='+',type=str,choices=['GMAO','NRL','MET','MeteoFr','JMA_adj','JMA_ens','EMC'],required=True)
parser.add_argument('--cycle',help='cycle to process',nargs='+',type=int,default=None,choices=[0,6,12,18],required=False)
parser.add_argument('--platform',help='platform to plot',type=str,required=True)
parser.add_argument('--obtype',help='observation types to include',nargs='+',type=str,default=None,required=False)
parser.add_argument('--channel',help='channel to process',nargs='+',type=int,default=None,required=False)
parser.add_argument('--savefigure',help='save figures',action='store_true',required=False)

args = parser.parse_args()

rootdir = args.rootdir
norm = args.norm
centers = args.centers
cycle = [0,6,12,18] if args.cycle is None else sorted(list(set(args.cycle)))
platform = args.platform
obtype = args.obtype
channel = args.channel
savefig = args.savefigure

cyclestr = ' '.join('%02dZ' % c for c in cycle)
if channel is not None:
    channelstr = ', '.join('%d' % c for c in channel)
ref_center = centers[0]

fcorrpkl = '%s/work/%s.%s.corr.pkl' % (rootdir,platform.lower(),norm)
if os.path.isfile(fcorrpkl):
    overwrite = input('%s exists, OVERWRITE [y/N]: ' % fcorrpkl)
else:
    overwrite = 'Y'

if overwrite.upper() in ['Y','YES']:
    # Read and select by cycles, obtypes and channels
    df = read_centers()
    # Compute stdev and correlations between centers
    df_stdv,df_corr = compute_std_corr(df)
    # Store as a pkl file
    os.remove(fcorrpkl)
    lutils.pickle(fcorrpkl,[df_stdv,df_corr])
else:
    # Unpickle a pkl file
    df_stdv,df_corr = lutils.unpickle(fcorrpkl)

df_corr.reset_index(inplace=True)
lons = df_corr['LONGITUDE'].values
lats = df_corr['LATITUDE'].values

cmap = plt.cm.get_cmap(name='coolwarm',lut=20)
proj = lmapping.Projection('mill',resolution='c',llcrnrlat=-80.,urcrnrlat=80.)
bmap = lmapping.createMap(proj)
xg,yg = bmap(lons,lats)

title_substr = '%s DJF 2014-15\n%s' % (cyclestr,platform)
if channel is not None:
    title_substr = '%s, ch. %s' % (title_substr,channelstr)

fsoi = loi.FSOI()

for center in centers[1:]:

    titlestr = '%s - %s correlation\n%s' % (fsoi.center_name[ref_center],fsoi.center_name[center],title_substr)
    plot_corr(center,df_corr[center],titlestr)

if savefig:
    plt.close('all')
else:
    plt.show()

sys.exit(0)
