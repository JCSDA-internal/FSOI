#!/usr/bin/env python

'''
get_metadata.py - List metadata such as platform, observation types and channels
'''

import sys
from argparse import ArgumentParser,ArgumentDefaultsHelpFormatter

sys.path.append('../lib')
import lib_utils as lutils

parser = ArgumentParser(description='Get metadata from a file',
                        formatter_class=ArgumentDefaultsHelpFormatter)
parser.add_argument('-f', '--filename',
                    help='filename to get metadata from', type=str, required=True)
args = parser.parse_args()

filename = args.filename
try:
    df = lutils.readHDF(filename, 'df')
except IOError:
    raise IOError('%s does not exist' % filename)
except Exception:
    raise Exception('Unknown exception in reading %s' % filename)

platforms = df.index.get_level_values('PLATFORM').unique()
for platform in sorted(platforms):
    print(platform)
    tmp = df.xs(platform, level='PLATFORM', drop_level=False)
    obtypes = tmp.index.get_level_values('OBTYPE').unique()
    msg = '\t| ' + ' '.join(obtypes)
    print(msg)
    if 'Tb' in obtypes:
        channels = tmp.index.get_level_values('CHANNEL').unique()
        msg = '\t| ' + ' '.join(map(str,sorted(channels)))
        print(msg)
    print('')

sys.exit(0)
