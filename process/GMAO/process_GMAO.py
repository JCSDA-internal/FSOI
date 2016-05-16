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
from netCDF4 import Dataset
from datetime import datetime,timedelta
from argparse import ArgumentParser,ArgumentDefaultsHelpFormatter

class ODS(object):

    def __init__(self,filename):
        try:
            self.file_ = Dataset(filename,'r')
        except RuntimeError,e:
            raise IOError(e.message + ' ' + filename)

    def read(self,only_good=True):
        for vname in self.file_.variables:
            if vname in ['days','syn_beg','syn_len']: continue
            tmp = self.file_.variables[vname][:]
            if vname in ['kt_names','kt_units','kx_names','kx_meta','qcx_names']:
                tmp2 = []
                for i in range(len(tmp)):
                    tmp2.append(''.join(tmp[i]).strip())
                tmp = tmp2
            exec('self.%s = tmp' % vname)

        if only_good:
            indx = self.qcexcl == 0
        else:
            indx = np.ma.logical_and(self.qcexcl >= 0,self.qcexcl <= 255)

        for name in ['lat','lon','lev','time','kt','kx','ks','xm','obs','omf','oma','xvec','qcexcl','qchist']:
            exec('self.%s = self.%s[indx]'%(name,name))

        self.nobs = len(self.kx)

        return self

    def close(self):
        try:
            self.file_.close()
        except RuntimeError,e:
            raise IOError(e.message + ' ' + filename)

def kt_def():
    kt = {
        4   : ['u', 'Upper-air zonal wind', 'm/sec'],
        5   : ['v', 'Upper-air meridional wind','m/sec'],
        11  : ['q', 'Upper-air specific humidity','g/kg'],
        12  : ['w10', 'Surface (10m) wind speed','m/sec'],
        17  : ['rr', 'Rain Rate','mm/hr'],
        18  : ['tpw', 'Total Precipitable Water',''],
        21  : ['col_o3', 'Total column ozone','DU'],
        22  : ['lyr_o3', 'Layer ozone','DU'],
        33  : ['ps', 'Surface (2m) pressure','hPa'],
        39  : ['sst', 'Sea-surface temperature','K'],
        40  : ['Tb', 'Brightness temperature','K'],
        44  : ['Tv', 'Upper-air virtual temperature','K'],
        89  : ['ba', 'Bending Angle','N'],
        101 : ['zt', 'Sub-surface temperature','C'],
        102 : ['zs', 'Sub-surface salinity',''],
        103 : ['ssh', 'Sea-surface height anomaly','m'],
        104 : ['zu', 'Sub-surface zonal velocity','m/s'],
        105 : ['zv', 'Sub-surface meridional velocity','m/s'],
        106 : ['ss', 'Synthetic Salinity','']
    }
    return kt

def kx_def():
    kx = {}
    for key in [120,220]:
        kx[key] = 'Radiosonde'
    for key in [221,229]:
        kx[key] = 'PIBAL'
    for key in [132,182,232]:
        kx[key] = 'Dropsonde'
    for key in [130,230]:
        kx[key] = 'AIREP'
    for key in [131,231]:
        kx[key] = 'ASDAR'
    for key in [133,233]:
        kx[key] = 'MDCARS'
    for key in [180,280]:
        kx[key] = 'Ship'
    for key in [282]:
        kx[key] = 'Moored_Buoy'
    for key in [181]:
        kx[key] = 'Land_Surface'
    for key in [187]:
        kx[key] = 'METAR'
    for key in [199,299]:
        kx[key] = 'Drifting_Buoy'
    for key in [223]:
        kx[key] = 'Profiler_Wind'
    for key in [224]:
        kx[key] = 'NEXRAD_Wind'
    for key in [242,243,245,246,250,252,253]:
        kx[key] = 'Geo_Wind'
    for key in [244]:
        kx[key] = 'AVHRR_Wind'
    for key in [257,258,259]:
        kx[key] = 'MODIS_Wind'
    for key in [285]:
        kx[key] = 'RAPIDSCAT_Wind'
    for key in [290]:
        kx[key] = 'ASCAT_Wind'
    for key in [3,4,42,43,722,740,741,743,744,745]:
        kx[key] = 'GPSRO'
    for key in [112,210]:
        kx[key] = 'TCBogus'

    return kx

def get_files(datadir,adate):
    vdate = adate + timedelta(hours=24)
    idate = adate - timedelta(hours=9)
    idatestr = idate.strftime('%Y%m%d_%Hz')
    vdatestr = vdate.strftime('%Y%m%d_%Hz')
    adatestr = adate.strftime('%Y%m%d_%Hz')
    strmatch = '.%s+%s-%s.' % (idatestr,vdatestr,adatestr)
    files = [f for f in os.listdir(datadir) if strmatch in f]
    return files

def main():

    BUFFER_LINES = 100000

    parser = ArgumentParser(description = 'Process GMAO data',formatter_class=ArgumentDefaultsHelpFormatter)
    parser.add_argument('-i','--indir',help='path to ODS directory',type=str,required=True)
    parser.add_argument('-o','--output',help='Processed GMAO file',type=str,required=True)
    parser.add_argument('-a','--adate',help='analysis date to process',metavar='YYYYMMDDHH',required=True)
    args = parser.parse_args()

    datapth = args.indir
    fname_out = args.output
    adate = datetime.strptime(args.adate,'%Y%m%d%H')

    kx = kx_def()
    kt = kt_def()

    fascii = open(fname_out,'w')

    datadir = os.path.join(datapth,adate.strftime('M%m'),adate.strftime('D%d'))
    flist = get_files(datadir,adate)
    nobs = 0
    bufr,lbufr = '',0
    for fname in flist:
        print 'processing %s' % fname

        platform = fname.split('.')[1].split('imp3_txe_')[-1].upper()

        fname = os.path.join(datadir,fname)
        ods = ODS(fname)
        ods = ods.read(only_good=True)
        ods.close()

        nobs += ods.nobs

        print 'platform = %s, nobs = %d' % (platform,ods.nobs)

        for o in range(ods.nobs):

            plat = kx[ods.kx[o]] if platform in ['CONV'] else platform
            obtype = kt[ods.kt[o]][0]
            channel = -999 if platform in ['CONV'] else np.int(ods.lev[o])
            lon = ods.lon[o] if ods.lon[o] >= 0.0 else ods.lon[o] + 360.0
            lat = ods.lat[o]
            if obtype == 'ps':
                lev = ods.obs[o]
            elif obtype == 'Tb':
                lev = -999.
            else:
                lev = ods.lev[o]
            imp = ods.xvec[o]
            omf = ods.omf[o]

            # PLATFORM OBTYPE LONGITUDE LATITUDE LEVEL IMPACT OMF
            line = '%-15s %-10s %5d %10.4f %10.4f %10.4f %15.8e %15.8e\n' % (plat,obtype,channel,lon,lat,lev,imp,omf)

            bufr += line
            lbufr += 1
            if lbufr >= BUFFER_LINES:
                fascii.writelines(bufr)
                bufr,lbufr = '',0

        if lbufr != 0:
            fascii.writelines(line)

    fascii.close()

    print 'Total obs used in %s = %d' % (adate.strftime('%Y%m%d%H'),nobs)

    sys.exit(0)

if __name__ == '__main__':
    main()
