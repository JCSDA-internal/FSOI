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
import gzip
import numpy as np
from datetime import datetime
from fortranformat import FortranRecordReader
from argparse import ArgumentParser,ArgumentDefaultsHelpFormatter

sys.path.extend(['../../lib', '../lib'])
import lib_utils as lutils
import lib_obimpact as loi

def kt_def():
    kt = {
          1  : ['ps','Surface Pressure','hPa'],
          2  : ['T','Temperature','K'],
          3  : ['rh','Relative Humidity','%'],
          4  : ['u','U-wind component','m/s'],
          5  : ['v','V-wind component','m/s'],
          10 : ['Tb','Brightness Temperature','K'],
          12 : ['X','Ground GPS',''], # 12 ==> Ground GPS, UNSURE what this is
          71 : ['ba','Bending Angle','N']
        }
    return kt

def parse_line(line,kt):

    fmtstr = 'i8,1x,e15.8,1x,e15.8,1x,e16.8,1x,f6.2,1x,f6.2,1x,f10.4,1x,i3,1x,i5,1x,i6,1x,e14.8,1x,f6.2,1x,a35'
    line_reader = FortranRecordReader(fmtstr)

    datain = line_reader.read(line)

    ob = datain[1]
    omf = datain[2]
    sens = datain[3]
    lat = datain[4]
    lon = datain[5]
    lev = datain[6]
    obtyp = datain[7]
    instyp = datain[8]
    oberr = datain[10]
    schar = datain[12]

    impact = omf * sens

    if obtyp == 10: # Radiances
        platform,channel = get_radiance(schar)
        if platform == 'UNKNOWN':
            print('MISSING RAD : ', platform, channel, ' | ',  schar)
    else: # Conventional
        platform,channel = get_conventional(instyp,schar)
        if platform == 'UNKNOWN':
            print('MISSING CONV: ', platform, instyp, ' | ', schar)

    if skip_ob(obtyp,instyp,oberr,impact):
        print('SKIPPING : ', line.strip())
        return None

    dataout = {}
    dataout['platform'] = platform
    dataout['channel'] = channel
    dataout['obtype'] = kt[obtyp][0]
    dataout['lat'] = lat
    dataout['lon'] = lon
    dataout['lev'] = -999. if lev == -9999.9999 else lev
    dataout['impact'] = impact
    dataout['omf'] = omf
    dataout['ob'] = ob
    dataout['oberr'] = oberr

    return dataout

def get_conventional(instyp,schar):

    schar = schar.upper()
    zchar = schar.split()

    platform = 'UNKNOWN'
    channel = -999

    if 'AIRCRAFT' in schar:
        platform = 'Aircraft'
    elif any(x in schar for x in [
        'GOES   3',
        'GOES   4',
        'GOES 206',
        'GOES 207',
        'GOES 209',
        'GOES 223',
        'MSG   3',
        'MSG   4'
        ]):
        platform = 'AVHRR_Wind'
    elif 'DROP' in schar:
        platform = 'Dropsonde'
    elif 'GPSRO' in schar:
        platform = 'GPSRO'
    elif 'GROUNDGPS' in schar:
        platform = 'GroundGPS'
    elif any(x in schar for x in [
        'GOES 783',
        'GOES 784',
        ]):
        platform = 'MODIS_Wind'
    elif 'GOES 854' in schar:
        platform = 'LEO-GEO'
    elif any(x in schar for x in [
        'ESA  54',
        'JMA 172',
        'MSG  57',
        'GOES 257',
        'GOES 259',
        ]):
        platform = 'Geo_Wind'
    elif any(x in schar for x in [
        'ASCAT   3',
        'ASCAT   4'
        ]):
        platform = 'ASCAT_Wind'
    elif 'KUSCAT 801' in schar:
        platform = 'KUSCAT'
    elif 'WINDSAT 283' in schar:
        platform = 'WINDSAT'
    elif 'TEMP' in schar:
        platform = 'Radiosonde'
    elif 'WINPRO' in schar:
        platform = 'Profiler_Wind'
    elif 'PILOT' in schar:
        platform = 'PILOT'
    elif 'SHIP' in schar:
        platform = 'Ship'
    elif 'SYNOP' in schar:
        platform = 'SYNOP'
    elif 'METAR' in schar:
        platform = 'METAR'
    elif 'BUOY' in schar:
        if instyp in [10210,10310]:
            platform = 'Moored_Buoy'
        elif instyp in [10212,10312]:
            platform = 'Drifting_Buoy'
        elif instyp in [10204]:
            platform = 'Platform_Buoy'
        else:
            platform = 'UNKNOWN'
    elif 'BOGUS' in schar:
        platform = 'TCBogus'

    return platform,channel

def get_radiance(schar):

    zchar = schar.split()

    platform = 'UNKNOWN'
    channel = int(zchar[-2].split('-')[-1])

    if 'EOS2 (Aqua) AIRS' in schar:
        platform = 'AIRS_Aqua'
    elif 'MetOp2 (A) ATOVS AMSUA' in schar:
        platform = 'AMSUA_METOP-A'
    elif 'MetOp1 (B) ATOVS AMSUA' in schar:
        platform = 'AMSUA_METOP-B'
    elif 'NOAA15 ATOVS AMSUA' in schar:
        platform = 'AMSUA_N15'
    elif 'NOAA16 ATOVS AMSUA' in schar:
        platform = 'AMSUA_N16'
    elif 'NOAA18 ATOVS AMSUA' in schar:
        platform = 'AMSUA_N18'
    elif 'NOAA19 ATOVS AMSUA' in schar:
        platform = 'AMSUA_N19'
    elif 'MetOp2 (A) ATOVS HIRS' in schar:
        platform = 'HIRS_METOP-A'
    elif 'MetOp1 (B) ATOVS HIRS' in schar:
        platform = 'HIRS_METOP-B'
    elif 'NOAA19 ATOVS HIRS' in schar:
        platform = 'HIRS_N19'
    elif any(x in schar for x in [
        'MetOp2 (A) ATOVS IASI',
        'MetOp2 (A) IASI'
        ]):
        platform = 'IASI_METOP-A'
    elif any(x in schar for x in [
        'MetOp1 (B) ATOVS IASI',
        'MetOp1 (B) IASI'
        ]):
        platform = 'IASI_METOP-B'
    elif 'JPSS0 (NPP) ATMS ATMS' in schar:
        platform = 'ATMS_NPP'
    elif 'JPSS0 (NPP) CrIS CrIS' in schar:
        platform = 'CrIS_NPP'
    elif 'MSG3 (MET10) SEVIRICLR' in schar:
        platform = 'SEVIRI_MSR'
    elif 'MTSAT2 MTSATCLR MTSATCLR' in schar:
        platform = 'MTSAT_CSR'
    elif 'METEOSAT7 MVIRICLR MVIRICLR' in schar:
        platform = 'MVIRI_CSR'
    elif 'MetOp2 (A) ATOVS AMSUB' in schar:
        platform = 'MHS_METOP-A'
    elif 'MetOp1 (B) ATOVS AMSUB' in schar:
        platform = 'MHS_METOP-B'
    elif 'NOAA18 ATOVS AMSUB' in schar:
        platform = 'MHS_N18'
    elif 'NOAA19 ATOVS AMSUB' in schar:
        platform = 'MHS_N19'
    elif any(x in schar for x in [
        'GOES13 GOESCLR GOESCLR',
        'GOES15 GOESCLR GOESCLR'
        ]):
        platform = 'GOES_CSR'

    return platform,channel

def skip_ob(obtyp,instyp,oberr,impact):

    # discard obs with very large impact
    if np.abs(impact) > 1.e-3:
        return True

    return False

def main():

    parser = ArgumentParser(description = 'Process UKMet file',formatter_class=ArgumentDefaultsHelpFormatter)
    parser.add_argument('-i','--input',help='Raw UKMet file',type=str,required=True)
    parser.add_argument('-o','--output',help='Processed UKMet file',type=str,required=True)
    parser.add_argument('-a','--adate',help='analysis date to process',metavar='YYYYMMDDHH',required=True)
    args = parser.parse_args()

    fname = args.input
    fname_out = args.output
    adate = datetime.strptime(args.adate,'%Y%m%d%H')

    try:
        fh = gzip.open(fname,'rb')
    except RuntimeError as e:
        raise IOError(e, fname)

    kt = kt_def()

    lines = fh.readlines()
    fh.close()

    bufr = []
    nobs = 0
    for line in lines:

        data = parse_line(line,kt)

        if data is None:
            continue

        nobs += 1

        plat = data['platform']
        channel = data['channel']
        obtype = data['obtype']
        lon = data['lon'] if data['lon'] >= 0.0 else data['lon'] + 360.0
        lat = data['lat']
        lev = data['lev']
        imp = data['impact']
        omf = data['omf']
        oberr = data['oberr']

        line = [plat,obtype,channel,lon,lat,lev,imp,omf,oberr]

        bufr.append(line)

    if bufr != []:
        df = loi.list_to_dataframe(adate,bufr)
        if os.path.isfile(fname_out): os.remove(fname_out)
        lutils.writeHDF(fname_out,'df',df,complevel=1,complib='zlib',fletcher32=True)

    print('Total obs = %d' % (nobs))

    sys.exit(0)

if __name__ == '__main__':
    main()
