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

from jma import jma

def main():

    BUFFER_LINES = 1000000

    parser = ArgumentParser(description = 'Read JMA file',formatter_class=ArgumentDefaultsHelpFormatter)
    parser.add_argument('-i','--indir',help='path to JMA data directory',type=str,required=True)
    parser.add_argument('-o','--outdir',help='path to output directory',type=str,required=True)
    parser.add_argument('-a','--adate',help='analysis date to process',metavar='YYYYMMDDHH',required=True)
    parser.add_argument('-f','--formulation',help='FSO formulation',choices=['ADJOINT','ENSEMBLE'],required=True)
    args = parser.parse_args()

    datapth = args.indir
    workdir = args.outdir
    adate = datetime.strptime(args.adate,'%Y%m%d%H')
    formulation = args.formulation

    fname_out = '%s/JMA_%s.txt' % (workdir,adate.strftime('%Y%m%d%H'))
    fascii = open(fname_out,'w')

    if formulation == 'ADJOINT':
        fname = os.path.join(datapth,'adj_fso_jma_%s00.dat' % adate.strftime('%Y%m%d%H'))
    elif formulation == 'ENSEMBLE':
        fname = os.path.join(datapth,'ens_fso_jma_%s00.dat' % adate.strftime('%Y%m%d%H'))
    formulation,idate,nobstot,nmetric = jma.get_header(fname,endian='big')
    obtype,platform,chan,lat,lon,lev,omf,oberr,imp = jma.get_data(fname,nobstot,nmetric,endian='big')

    bufr, lbufr = '', 0
    for o in range(nobstot):

        obtyp = ''.join(obtype[o]).strip()
        plat = ''.join(platform[o]).strip()

        line = '%-15s %-10s %5d %10.4f %10.4f %10.4f %15.8e %15.8e\n' % (plat,obtyp,chan[o],lon[o],lat[o],lev[o],imp[o][0],omf[o])

        bufr += line
        lbufr += 1
        if lbufr >= BUFFER_LINES:
            fascii.writelines(bufr)
            bufr = ''
            lbufr = 0

    if lbufr != 0:
        fascii.writelines(bufr)

    fascii.close()

    print 'Total obs used in %s = %d' % (adate.strftime('%Y%m%d%H'),nobstot)

    sys.exit(0)

if __name__ == '__main__':
    main()
