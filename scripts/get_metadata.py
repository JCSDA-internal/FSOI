#!/usr/bin/env python

 ###############################################################
 # < next few lines under version control, D O  N O T  E D I T >
 # $Date$
 # $Revision$
 # $Author$
 # $Id$
 ###############################################################

'''
get_metadata.py - List metadata such as platform, observation types and channels
'''

import sys
from argparse import ArgumentParser,ArgumentDefaultsHelpFormatter

import lib_utils as lutils

parser = ArgumentParser(description = 'Get metadata from a center',formatter_class=ArgumentDefaultsHelpFormatter)
parser.add_argument('-c','--center',help='originating center',type=str,required=True,choices=['EMC','GMAO','NRL','JMA_adj','JMA_ens','MET'])
parser.add_argument('-r','--rootdir',help='root path to directory',type=str,default='/scratch3/NCEPDEV/stmp2/Rahul.Mahajan/test/Thomas.Auligne/FSOI',required=False)
args = parser.parse_args()

rootdir = args.rootdir
center = args.center

fname = '%s/work/%s/bulk_stats.h5' % (rootdir,center)
df = lutils.readHDF(fname,'df')

platforms = df.index.get_level_values('PLATFORM').unique()
for platform in sorted(platforms):
    print '%s' % platform
    tmp = df.xs(platform,level='PLATFORM',drop_level=False)
    obtypes = tmp.index.get_level_values('OBTYPE').unique()
    print '   | ' + ' '.join(obtypes)
    if 'Tb' in obtypes:
        channels = tmp.index.get_level_values('CHANNEL').unique()
        print '   | ' + ' '.join(map(str,sorted(channels)))
    print

sys.exit(0)