#!/usr/bin/env python
###############################################################
# < next few lines under version control, D O  N O T  E D I T >
# $Date$
# $Revision$
# $Author$
# $Id$
###############################################################

import os
import sys
import numpy as np
from datetime import datetime
from argparse import ArgumentParser,ArgumentDefaultsHelpFormatter

from emc import emc

import lib_utils as lutils

sys.path.append('../../scripts')
import lib_obimpact as loi

def kt_def():
    kt = {
        4   : ['u', 'Upper-air zonal wind', 'm/sec'],
        5	: ['v', 'Upper-air meridional wind','m/sec'],
        11	: ['q', 'Upper-air specific humidity','g/kg'],
        12	: ['w10', 'Surface (10m) wind speed','m/sec'],
        17	: ['rr', 'Rain Rate','mm/hr'],
        18	: ['tpw', 'Total Precipitable Water',''],
        21	: ['col_o3', 'Total column ozone','DU'],
        22	: ['lyr_o3', 'Layer ozone','DU'],
        33	: ['ps', 'Surface (2m) pressure','hPa'],
        39	: ['sst', 'Sea-surface temperature','K'],
        40	: ['Tb', 'Brightness temperature','K'],
        44	: ['Tv', 'Upper-air virtual temperature','K'],
        89	: ['ba', 'Bending Angle','N'],
        101	: ['zt', 'Sub-surface temperature','C'],
        102	: ['zs', 'Sub-surface salinity',''],
        103	: ['ssh', 'Sea-surface height anomaly','m'],
        104	: ['zu', 'Sub-surface zonal velocity','m/s'],
        105	: ['zv', 'Sub-surface meridional velocity','m/s'],
        106	: ['ss', 'Synthetic Salinity','']
    }
    return kt

def get_platform_rad(plat):

    platform = plat.upper()

    if 'CRIS' in platform:
        platform.replace('CRIS','CrIS')
    elif 'AIRS281SUBSET' in platform:
        platform.replace('AIRS281SUBSET','AIRS')
    elif 'IASI616' in platform:
        platform.replace('IASI616','IASI')
    elif 'SEVIRI_M' in platform:
        platform.replace('SEVIRI_M','SEVIRI')

    return platform

def get_platform_con(plat):

    platform = 'UNKNOWN'

    if plat in map(str,[122,126,191,285,286]):
        platform = 'UNKNOWN'
    elif plat in map(str,[122,132]):
        platform = 'Dropsonde'
    elif plat in map(str,[150,152]):
        platform = 'SPSSMI_UNKNOWN'
    elif plat in map(str,[151,156,157,158,159,164,165,174,175]):
        platform = 'GOESND_UNKNOWN'
    elif plat in map(str,[170,270]):
        platform = 'NACELLE_UNKNOWN'
    elif plat in map(str,[171,271]):
        platform = 'TALL_TOWER_UNKNOWN'
    elif plat in map(str,[183,194,284,294]):
        platform = 'Land_Marine_UNKNOWN'
    elif plat in map(str,[222]):
        platform = 'ADPUPA_UNKNOWN'
    elif plat in map(str,[111,112,210]):
        platform = 'TCBogus'
    elif plat in map(str,[120,220]):
        platform = 'Radiosonde'
    elif plat in map(str,[130,131,133,134,135,230,231,233,234,235]):
        platform = 'Aircraft'
    elif plat in map(str,[153]):
        platform = 'GPS_PW'
    elif plat in map(str,[180,182,280]):
        platform = 'Mobile_Marine_Surface'
    elif plat in map(str,[181,187,188,192,193,195,281,287,288,292,293,295]):
        platform = 'Land_Surface'
    elif plat in map(str,[221]):
        platform = 'PIBAL'
    elif plat in map(str,[223,227,228,229]):
        platform = 'Profiler_Wind'
    elif plat in map(str,[224]):
        platform = 'NEXRAD_Wind'
    elif plat in map(str,list(np.arange(240,261))):
        platform = 'Sat_Wind'
    elif plat in map(str,[282]):
        platform = 'Moored_Buoy'
    elif plat in map(str,[289]):
        platform = 'WINDSAT_Wind'
    elif plat in map(str,[290]):
        platform = 'ASCAT_Wind'
    elif plat in map(str,[296]):
        platform = 'RAPIDSCAT_Wind'
    elif plat in map(str,[3,4,41,42,722,723,740,741,742,743,744,745]):
        platform = 'GPSRO'
    elif plat in map(str,list(np.arange(701,722)))+map(str,list(np.arange(723,739))):
        platform = 'Ozone'
    else:
        print 'UNKNOWN : ', plat

    return platform

def main():

    parser = ArgumentParser(description = 'Process EMC file',formatter_class=ArgumentDefaultsHelpFormatter)
    parser.add_argument('-i','--input',help='Raw EMC file',type=str,required=True)
    parser.add_argument('-o','--output',help='Processed EMC HDF file',type=str,required=True)
    parser.add_argument('-a','--adate',help='analysis date to process',metavar='YYYYMMDDHH',required=True)
    args = parser.parse_args()

    fname = args.input
    fname_out = args.output
    adate = datetime.strptime(args.adate,'%Y%m%d%H')

    idate,nobscon,nobsoz,nobssat,npred,nens = emc.get_header(fname,endian='big')
    nobs = nobscon + nobsoz + nobssat
    obtype,platform,chan,lat,lon,lev,omf,oberr,imp = emc.get_data(fname,nobs,npred,nens,endian='big')

    obtype = (obtype.tostring()).replace('\x00','')[:-1].split('|')
    platform = (platform.tostring()).replace('\x00','')[:-1].split('|')

    bufr = []
    for o in range(nobs):

        obtyp = ''.join(obtype[o]).strip()
        platf = ''.join(platform[o]).strip()
        if o < (nobscon+nobsoz):
            plat = get_platform_con(platf)
            if plat in 'UNKNOWN':
                print o+1,plat,platf
        else:
            plat = get_platform_rad(platf)

        lon[o] = lon[o] if lon[o] >= 0.0 else lon[o] + 360.0

        line = [plat,obtyp,chan[o],lon[o],lat[o],lev[o],imp[o][0],omf[o],oberr[o]]

        bufr.append(line)

    if bufr != []:
        df = loi.list_to_dataframe(adate,bufr)
        if os.path.isfile(fname_out): os.remove(fname_out)
        lutils.writeHDF(fname_out,'df',df,complevel=1,complib='zlib',fletcher32=True)

    print 'Total obs = %d' % (nobs)

    sys.exit(0)

if __name__ == '__main__':
    main()
