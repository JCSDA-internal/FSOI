#!/usr/bin/env python
###############################################################
# < next few lines under version control, D O  N O T  E D I T >
# $Date$
# $Revision$
# $Author$
# $Id$
###############################################################

import sys
from argparse import ArgumentParser,ArgumentDefaultsHelpFormatter

from jma import jma

def main():

    BUFFER_LINES = 1000000

    parser = ArgumentParser(description = 'Process JMA file',formatter_class=ArgumentDefaultsHelpFormatter)
    parser.add_argument('-i','--input',help='Raw JMA file',type=str,required=True)
    parser.add_argument('-o','--output',help='Processed JMA file',type=str,required=True)
    args = parser.parse_args()

    fname = args.input
    fname_out = args.output

    fascii = open(fname_out,'w')

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

    print 'Total obs = %d' % (nobstot)

    sys.exit(0)

if __name__ == '__main__':
    main()
