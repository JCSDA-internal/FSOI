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
from datetime import datetime
from argparse import ArgumentParser,ArgumentDefaultsHelpFormatter
from jma import jma

sys.path.append('../../lib')
import fsoi.stats.lib_utils as lutils
import fsoi.stats.lib_obimpact as loi

if __name__ == '__main__':

    parser = ArgumentParser(description = 'Process JMA file',formatter_class=ArgumentDefaultsHelpFormatter)
    parser.add_argument('-i','--input',help='Raw JMA file',type=str,required=True)
    parser.add_argument('-o','--output',help='Processed JMA HDF file',type=str,required=True)
    parser.add_argument('-a','--adate',help='analysis date to process',metavar='YYYYMMDDHH',required=True)
    args = parser.parse_args()

    fname = args.input
    fname_out = args.output
    adate = datetime.strptime(args.adate,'%Y%m%d%H')

    formulation,idate,nobstot,nmetric = jma.get_header(fname,endian='big')
    obtype,platform,chan,lat,lon,lev,omf,oberr,imp = jma.get_data(fname,nobstot,nmetric,endian='big')

    obtype = (obtype.tostring()).replace('\x00','')[:-1].split('|')
    platform = (platform.tostring()).replace('\x00','')[:-1].split('|')

    bufr = []
    for o in range(nobstot):

        obtyp = ''.join(obtype[o]).strip()
        plat = ''.join(platform[o]).strip()

        lon[o] = lon[o] if lon[o] >= 0.0 else lon[o] + 360.0

        line = [plat,obtyp,chan[o],lon[o],lat[o],lev[o],imp[o][0],omf[o],oberr[o]]

        bufr.append(line)

    if bufr != []:
        df = loi.list_to_dataframe(adate,bufr)
        if os.path.isfile(fname_out): os.remove(fname_out)
        lutils.writeHDF(fname_out,'df',df,complevel=1,complib='zlib',fletcher32=True)

    print('Total obs = %d' % (nobstot))

    sys.exit(0)
