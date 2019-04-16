#!/usr/bin/env python

'''
extract_platform_bulk.py - extract a platform from bulk_stats and write out
'''

import os
import sys
import numpy as np
from argparse import ArgumentParser,ArgumentDefaultsHelpFormatter

sys.path.append('../lib')
import lib_utils as lutils
import lib_obimpact as loi

if __name__ == '__main__':

    parser = ArgumentParser(description = 'Extract a platform from bulk HDF file, and write out',formatter_class=ArgumentDefaultsHelpFormatter)
    parser.add_argument('--center',help='originating center',type=str,choices=['GMAO','NRL','MET','MeteoFr','JMA_adj','JMA_ens','EMC'],required=True)
    parser.add_argument('--platform',help='platform to extract and bin',type=str,required=True)
    parser.add_argument('--norm',help='metric norm',type=str,default='dry',choices=['dry','moist'],required=False)
    parser.add_argument('--rootdir',help='root path to directory',type=str,default='/scratch3/NCEPDEV/stmp2/Rahul.Mahajan/test/Thomas.Auligne/FSOI',required=False)

    args = parser.parse_args()

    center = args.center
    rootdir = args.rootdir
    norm = args.norm
    platform = args.platform

    search_str = ['PLATFORM="%s"' % (platform)]

    fbulk = '%s/work/%s/%s/bulk_stats.h5' % (rootdir,center,norm)
    df = lutils.readHDF(fbulk,'df',where=search_str)
    if platform not in df.index.get_level_values('PLATFORM').unique():
        print('%s does not exist in %s' % (platform,fbulk))
        print('ABORTING')
        raise Exception()

    df.reset_index(inplace=True)
    df.drop('PLATFORM',axis=1,inplace=True)
    df = df.groupby(['DATETIME','OBTYPE','CHANNEL']).agg('sum')

    fbinned = '%s/work/%s/%s/%s.h5' % (rootdir,center,norm,platform.lower())
    if os.path.isfile(fbinned): os.remove(fbinned)
    lutils.writeHDF(fbinned,'df',df,complevel=1,complib='zlib',fletcher32=True)

    sys.exit(0)
