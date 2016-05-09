#!/usr/bin/env python

 ###############################################################
 # < next few lines under version control, D O  N O T  E D I T >
 # $Date$
 # $Revision$
 # $Author$
 # $Id$
 ###############################################################

 '''
get_platforms.py - List platforms and observation types
 '''

import sys
from argparse import ArgumentParser,ArgumentDefaultsHelpFormatter

import lib_obimpact as loi

parser = ArgumentParser(description = 'Get platforms and observation types',formatter_class=ArgumentDefaultsHelpFormatter)
parser.add_argument('-c','--center',help='originating center',type=str,required=True,choices=['EMC','GMAO','NRL','JMA_adj','JMA_ens','MET'])
parser.add_argument('-r','--rootdir',help='root path to directory',type=str,default='/scratch3/NCEPDEV/stmp2/Rahul.Mahajan/test/Thomas.Auligne/FSOI',required=False)
parser.add_argument('-o','--obtypes',help='show observation type for each platform',action='store_true',required=False)
args = parser.parse_args()

rootdir = args.rootdir
center = args.center
show_obtypes = args.obtypes

fname = '%s/work/%s/bulk_stats.h5' % (rootdir,center)
df = loi.loadDF(fname)

platforms = df.index.get_level_values('PLATFORM').unique()
for platform in sorted(platforms):
    print '   %s' % platform
    if show_obtypes:
        tmp = df.xs(platform,level='PLATFORM',drop_level=False)
        obtypes = tmp.index.get_level_values('OBTYPE').unique()
        for obtype in obtypes:
            print '     %s' % obtype

sys.exit(0)
