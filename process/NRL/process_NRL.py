#!/usr/bin/env python
###############################################################
# < next few lines under version control, D O  N O T  E D I T >
# $Date$
# $Revision$
# $Author$
# $Id$
###############################################################

import sys
import numpy as np
from Scientific.IO import FortranFormat as ff
from argparse import ArgumentParser,ArgumentDefaultsHelpFormatter

def kt_def():
    kt = {
          1  : ['z','Geopotential Height','m'],
          2  : ['T','Temperature','K'],
          3  : ['u','U-wind component','m/s'],
          4  : ['v','V-wind component','m/s'],
          5  : ['q','Humidity',''],
          8  : ['wspd','Surface Wind Speed','m/s'],
          11 : ['ps','Surface Pressure','hPa'],
          13 : ['Tb','Brightness Temperature','K'],
          14 : ['tpw','Total Precipitable Water',''],
          18 : ['ba','Bending Angle','N'],
        }
    return kt

def kx_def():
    kx = {}
    kx[1] = 'Land_Surface'
    kx[10] = ['Ship','Drifting_Buoy','Moored_Buoy']
    for key in [20,23,121]:
        kx[key] = 'MIL_ACARS'
    for key in [25,26,30,31,32,33,34,131,132]:
        kx[key] = 'AIREP'
    for key in [35,36,37,38,136,137]:
        kx[key] = 'AMDAR'
    for key in [45,46,47,48,146,147]:
        kx[key] = 'MDCARS'
    for key in [50,51,52,53,54,55,56,57,58,59,65,66]:
        kx[key] = 'Sat_Wind'
    kx[60] = 'SSMI_Wind'
    kx[67] = 'R/S_AMV'
    for key in [70,71]:
        kx[key] = 'SCAT_Wind'
    kx[72] = 'WINDSAT'
    kx[73] = 'ASCAT_Wind'
    for key in [80,81,88]:
        kx[key] = 'MODIS_Wind'
    for key in [82,83,84,85,86,87]:
        kx[key] = 'AVHRR_Wind'
    kx[89] = 'LEO-GEO'
    kx[90] = 'UW_wiIR'
    kx[101] = ['Radiosonde','PIBAL','Dropsonde']
    kx[125] = 'SSMI_PRH'
    kx[126] = 'WINDSAT_PRH'
    kx[179] = 'GPSRO'
    kx[184] = 'MHS'
    kx[185] = 'SSMIS'
    kx[186] = 'UAS'
    kx[187] = 'AIRS'
    kx[188] = 'IASI'
    kx[190] = 'TCBogus'
    kx[194] = 'SEVIRI'
    kx[196] = 'CrIS'
    kx[197] = 'ATMS'
    kx[210] = 'AMSUA'
    kx[250] = 'SSMI_TPW'
    kx[251] = 'WINDSAT_TPW'

    return kx

def parse_line(line,kt,kx):

    fmtstr = 'i7,f9.3,1x,f8.2,1x,f8.2,1x,f8.2,f9.3,1x,f9.2,1x,f9.2,1x,f9.2,1x,f11.5,1x,i2,1x,i3,4x,i2,4x,i1,3x,i5,2x,a16,a12,4x,i1,2x,i1,3x,i1,1x,e13.6,1x,e13.6,1x,e13.6,1x,e13.6'
    fmt = ff.FortranFormat(fmtstr)

    datain = ff.FortranLine(line,fmt)

    ob = datain[1]
    omf = datain[4]
    oberr = datain[5]
    lat = datain[7]
    lon = datain[8]
    lev = datain[9]
    obtyp = datain[10]
    instyp = datain[11]
    irflag = datain[13]
    schar = datain[15] + '  ' + datain[16]
    num_reject = datain[19]
    resid = datain[22]
    sens = datain[23]

    impact = omf * sens

    if skip_ob(instyp,oberr,num_reject,impact):
        print line.strip()
        return None

    platform,channel = get_platform_channel(instyp,schar,kx)

    dataout = {}
    dataout['platform'] = platform
    dataout['channel'] = channel
    dataout['obtype'] = kt[obtyp][0]
    dataout['lat'] = lat
    dataout['lon'] = lon
    dataout['lev'] = lev
    dataout['impact'] = impact
    dataout['omf'] = omf
    dataout['ob'] = ob
    dataout['oberr'] = oberr
    dataout['oma'] = resid

    return dataout

def skip_ob(instyp,oberr,num_reject,impact):

    # discard observations with very large observation error
    #if oberr > 1000.:
    #    return True

    # discard rejected observations
    #if num_reject != 0:
    #    return True

    # discard [land_surface,ship] obs with zero impact
    if instyp in [1,10]:
        if impact == 0.:
            return True

    return False

def get_platform_channel(instyp,schar,kx):

    platform = 'UNKNOWN'
    channel = -999

    schar = schar.upper()

    platform = kx[instyp]

    if instyp in [10]:
        if 'BUOY' in schar:
            platform = 'Moored_Buoy'
        elif 'DRIFTER' in schar:
            platform = 'Drifting_Buoy'
        else:
            platform = 'Ship'

    elif instyp in [60]:
        if '13' in schar:
            platform = 'SSMI_13'
        elif '14' in schar:
            platform = 'SSMI_14'
        elif '15' in schar:
            platform = 'SSMI_15'

    elif instyp in [101]:
        if 'RECO' in schar:
            platform = 'Dropsonde'
        elif 'PIBAL' in schar:
            platform = 'PIBAL'
        else:
            platform = 'Radiosonde'

#   elif instyp in [50,51,52,53,54,55,56,57,58,59,65,66]:
#       platform = 'Sat_Wind'
#       if 'MET9' in schar:
#           platform = 'MET9'

    if platform in ['AMSUA']:
        if 'NOAA15' in schar:
            platform = '%s_N15' % platform
        elif 'NOAA16' in schar:
            platform = '%s_N16' % platform
        elif 'NOAA18' in schar:
            platform = '%s_N18' % platform
        elif 'NOAA19' in schar:
            platform = '%s_N19' % platform
        elif 'METOPA' in schar:
            platform = '%s_METOP-A' % platform
        elif 'METOPB' in schar:
            platform = '%s_METOP-B' % platform

        chanmin,chanmax = 1,16
        for ichan in range(chanmin,chanmax):
            if 'CH%2s' % ichan in schar:
                break
        if ichan != chanmax:
            channel = ichan

    elif platform in ['IASI']:
        if 'METOPA' in schar:
            platform = '%s_METOP-A' % platform
        elif 'METOPB' in schar:
            platform = '%s_METOP-B' % platform

        chanmin,chanmax = 51,412
        for ichan in range(chanmin,chanmax):
            if 'CH%4s' % ichan in schar:
                break
        if ichan != chanmax:
            channel = ichan

    elif platform in ['CrIS']:
        platform = '%s_NPP' % platform
        chanmin,chanmax = 1,1143
        for ichan in range(chanmin,chanmax):
            if 'CH%5s' % ichan in schar:
                break
        if ichan != chanmax:
            channel = ichan

    elif platform in ['ATMS']:
        platform = '%s_NPP' % platform
        chanmin,chanmax = 1,23
        for ichan in range(chanmin,chanmax):
            if 'CH%5s' % ichan in schar:
                break
        if ichan != chanmax:
            channel = ichan

    elif platform in ['MHS']:
        if 'NOAA18' in schar:
            platform = '%s_N18' % platform
        elif 'NOAA19' in schar:
            platform = '%s_N19' % platform
        elif 'METOPA' in schar:
            platform = '%s_METOP-A' % platform
        elif 'METOPB' in schar:
            platform = '%s_METOP-B' % platform

        chanmin,chanmax = 4,6
        for ichan in range(chanmin,chanmax):
            if 'CH%5s' % ichan in schar:
                break
        if ichan != chanmax:
            channel = ichan

    elif platform in ['SSMIS']:
        chanmin,chanmax = 2,25
        for ichan in range(chanmin,chanmax):
            if 'CH%3s' % ichan in schar:
                break
        if ichan != chanmax:
            channel = ichan

    return platform,channel

def main():

    BUFFER_LINES = 100000

    parser = ArgumentParser(description = 'Process NRL file',formatter_class=ArgumentDefaultsHelpFormatter)
    parser.add_argument('-i','--input',help='Raw NRL file',type=str,required=True)
    parser.add_argument('-o','--output',help='Processed NRL file',type=str,required=True)
    args = parser.parse_args()

    fname = args.input
    fname_out = args.output

    fascii = open(fname_out,'w')

    nobs = 0

    try:
        fh = open(fname,'rb')
    except RuntimeError,e:
        raise IOError(e.messaage + ' ' + fname)

    for _ in range(75):
        fh.readline()
    EOF = False

    kt = kt_def()
    kx = kx_def()

    lines = fh.readlines()
    bufr,lbufr = '',0
    for line in lines:

        data = parse_line(line,kt,kx)

        if data is None:
            continue

        nobs += 1

        plat = data['platform']
        channel = data['channel']
        obtype = data['obtype']
        lon = data['lon']
        lat = data['lat']
        lev = data['lev']
        imp = data['impact']
        omf = data['omf']

        # PLATFORM OBTYPE LONGITUDE LATITUDE LEVEL IMPACT OMF
        #line = '%-15s %-15s %10.4f %10.4f %10.4f %15.8e %15.8e\n' % (plat,obtype,lon,lat,lev,imp,omf)
        line = '%-15s %-10s %5d %10.4f %10.4f %10.4f %15.8e %15.8e\n' % (plat,obtype,channel,lon,lat,lev,imp,omf)

        bufr += line
        lbufr += 1
        if lbufr >= BUFFER_LINES:
            fascii.writelines(bufr)
            bufr = ''
            lbufr = 0

    if lbufr != 0:
        fascii.writelines(bufr)

    fh.close()
    fascii.close()

    print 'Total obs = %d' % (nobs)

    sys.exit(0)

if __name__ == '__main__':
    main()
