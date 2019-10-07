#!/usr/bin/python

"""
Python code to process gps data and generate h5 file

Usage:
python innovar_gps_io.py -d date-time -i input-loc -r ar_run [-s save-dir] [-n ndays]
"""

import glob
import os.path
import pkgutil
import h5py
import numpy as np
import pandas as pd
import yaml

REAL_SIZE = 8
REAL_TYPE = 'float%d' % (8 * REAL_SIZE)

MISSING = float(-999.99)

# get vertical (y-axis) binning  -- in mb pressure: {min,max,binsize}
# ly = {'min':float(-1000), 'max':float(70000), 'bin':float(1000)}
LY = {'min': float(-1250), 'max': float(100000), 'bin': float(2500)}
LY['num'] = int((LY['max'] - LY['min']) / LY['bin'] + 1)
LY['bins'] = LY['min'] + LY['bin'] / 2. + np.arange(LY['num']) * LY['bin']

# get x-axis binning latitudinal --- values in degrees
LX = {'min': float(-90), 'max': float(90), 'bin': float(5)}
LX['num'] = int((LX['max'] - LX['min']) / LX['bin'] + 1)
LX['bins'] = LX['min'] + np.arange(LX['num']) * LX['bin']

# WMO Common Code Table C-2: Radiosonde/Sounding System
# 'sat' matches at least part of the name in the c_db_ob column of the obs_sens_ops*.txt.bz2 file
# 'sat_id' is the satellite common code
# 'display_name' will be used in image filenames and plot labels

GPS = yaml.full_load(pkgutil.get_data('fsoi', 'stats/innovar_gps_io.yaml'))

GPS_TYPE = GPS['gps_type']
GPS_CATEGORIES = GPS['gps_categories']

KNOWN_GPS = []
KNOWN_GPS_ID = []
KNOWN_GPS_NAME = []
for t in GPS_TYPE:
    KNOWN_GPS.extend(GPS_TYPE[t]['sat'])
    KNOWN_GPS_ID.extend(GPS_TYPE[t]['sat_id'])
    KNOWN_GPS_NAME.extend(GPS_TYPE[t]['display_name'])


def main(filepath, cdtg, number_of_days, out_dir):
    """
    Main
    :param filepath:
    :param cdtg:
    :param number_of_days:
    :param out_dir:
    :return:
    """
    # initialization
    dtg_index, _ = time_window(number_of_days, cdtg)
    for dtg in dtg_index:

        # potential input file
        filename = filepath

        # this is the file for I/O
        output_path = os.path.join(out_dir, 'g' + dtg)
        output_file = os.path.join(out_dir, 'g' + dtg, 'global_gps_stats_' + dtg + '.h5')

        # FNMOC has "dead" links which glob thinks are files unless checked
        if not filename or (filename and not os.path.exists(filename)):
            if not os.path.exists(output_file):
                print(" at " + dtg + " no innovation or ob sensitivity files ")
                print(" or previous output: " + output_file)
                continue

        # read previous output file if it exists
        if os.path.exists(output_file):
            glb, sens_on = read_statistics(output_file)
            # if previous output file does not have fsoi data and
            # fsoi data is available, read and append the fsoi data
            if filename and not sens_on:
                fsoi_glb, sens_on = read_file(filename, append_fsoi=True)
                if sens_on:
                    write_file(fsoi_glb, output_path, output_file)
        # if there isn't a previous output file, create it
        else:
            glb, sens_on = read_file(filename)
            write_file(glb, output_path, output_file)


def initialize_data(dtg_index=False, fsoi=False):
    """
    Initialize data
    :param dtg_index:
    :param fsoi:
    :return:
    """
    # initialize summary data structure

    fields_2d = ['fg_depar', 'stdv_fg_depar', 'cnt', 'nob']
    if fsoi:
        fields_2d += ['ob_sens', 'sens_cnt']

    #  will reduce this to three groupings before plotting
    fields_3d = ['zonal_fg_depar', 'zonal_stdv_fg_depar', 'zonal_cnt']
    if fsoi:
        fields_3d += ['zonal_ob_sens', 'zonal_sens_cnt']

    d = {}
    d['times'] = []
    d['sat_ids'] = KNOWN_GPS_ID
    for afield in fields_2d:
        d[afield] = np.zeros((LY['num'], len(GPS_TYPE)), dtype=REAL_TYPE)
    for afield in fields_3d:
        d[afield] = np.zeros((LY['num'], LX['num'], len(GPS_TYPE)), dtype=REAL_TYPE)

    if dtg_index:
        d['dtg_cnt'] = np.zeros((len(dtg_index)), dtype=REAL_TYPE)
        d['sensor_dtg_cnt'] = np.zeros((len(dtg_index), len(GPS_TYPE)), dtype=REAL_TYPE)

    return d


def get_file_names(dtg, filepath):
    """
    Get file names
    :param dtg:
    :param filepath:
    :return:
    """
    filename = os.path.join(filepath, 'g' + dtg, 'obs_sens_*' + dtg + '*.txt*')
    filenames = glob.glob(filename)
    if not filenames:
        filename = None
    else:
        filename = filenames[0]

        # if no ob impact file found try FNMOC naming convention
    if not filename:
        filename = os.path.join(filepath, 'g' + dtg, dtg + '*.txt*')
        filenames = glob.glob(filename)
        if not filenames:
            filename = None
        else:
            filename = filenames[0]

            # try to get O-B statistics
    if not filename:
        filename1 = os.path.join(filepath, 'g' + dtg, 'innovar_1_' + dtg + '*')
        filename2 = os.path.join(filepath, 'innovar_gps_1_' + dtg + '*')
        filenames = glob.glob(filename1) + glob.glob(filename2)
        if not filenames:
            filename = None
        else:
            filename = filenames[0]

    return filename


def read_statistics(output_file):
    """
    Read statistics
    :param output_file:
    :return:
    """
    # begin reading previous output
    print("Reading output file...  " + output_file)

    f = h5py.File(output_file, 'r')
    if "zonal_ob_sens" not in f.keys():
        print(" no FSOI in H5 file ")
        sens_on = False
    else:
        sens_on = True

    data = {}
    for k in f:
        data[k] = np.asarray(f[k])

    f.close()

    # print ' printing the means for latitude ', ly['bins'][10]
    # print ("%9.2f"*int(gps_types))%tuple(glb['fg_depar'][10,:])
    return data, sens_on


def read_file(filename, append_fsoi=False):
    """
    Read a file
    :param filename:
    :param append_fsoi:
    :return:
    """
    print("Reading observation statistics file...  " + filename)

    nrl_data = pd.read_hdf(filename)

    # Get the data
    # data = list(f[a_group_key])

    # extract innovation header

    keys = nrl_data.keys()
    print(keys)
    sens_on = 'SENS' in keys

    if append_fsoi and not sens_on:
        glb = None
        return glb, sens_on

    last_rec = {'lat': np.float(0),
                'lon': np.float(0),
                'time': np.float(0),
                'sensor': ' '}

    # initialize local - individual dtg fg_depar & stdv
    single_profile = np.zeros((LY['num'], len(GPS_TYPE)))
    data_count = 0
    glb = initialize_data(fsoi=sens_on)

    row_number = 0

    while row_number < len(nrl_data.index):

        if 'GPS-RO' in nrl_data.at[row_number, 'C_PF'] and \
                int(nrl_data.at[row_number, 'ICHK']) == 0 and \
                int(nrl_data.at[row_number, 'REJ']) == 0:

            data_count += 1

            # find vertical bin
            impact_h = float(nrl_data.at[row_number, 'T_BK'])
            rnd_y = float(np.round((impact_h - LY['min']) / LY['bin'])) * LY['bin'] + LY['min']
            yidx = int((rnd_y - LY['min']) / LY['bin'])

            if yidx < 0:
                yidx = 0
            elif yidx >= LY['num']:
                yidx = LY['num'] - 1
            else:
                print('impact height outside range(val,min,max): ', impact_h, LY['min'], LY['max'])
                print('could not determine vertical index')
                continue
            # find latitude index
            lat = float(nrl_data.at[row_number, 'LATITUDE'])
            rnd_x = float(np.round((lat -
                                    LX['min']) / LX['bin'])) * \
                    LX['bin'] + LX['min']
            xidx = int(round((rnd_x - LX['min']) / LX['bin']))

            lon = np.float(nrl_data.at[row_number, 'LONGITUDE'])
            time = np.float(nrl_data.at[row_number, 'IDT'])
            sensor = nrl_data.at[row_number, 'C_DB']

            # which GPS sensor and satellite is it
            sensor_match = False
            for gps_index, aval in enumerate(KNOWN_GPS):
                if aval in nrl_data.at[row_number, 'C_DB']:
                    sensor_match = True
                    break
            # if we don't check this, it will match a non-matching sensor to the last index
            if not sensor_match:
                print(' ... could not recognize sensor: ' + sensor)
                continue

            # GPS bending angle innovation normalized by background
            xiv = 100.0 * np.float(nrl_data.at[row_number, 'OMF']) / \
                  np.float(nrl_data.at[row_number, 'BK'])

            if lat != last_rec['lat'] and lon != last_rec['lon'] and \
                    time != last_rec['time'] and sensor != last_rec['sensor']:
                last_rec = {'lat': lat,
                            'lon': lon,
                            'time': time,
                            'sensor': sensor}
                single_profile = np.zeros((LY['num'], len(GPS_TYPE)))

            location_1d = (yidx,)
            location_2d = (yidx, gps_index)

            if single_profile[location_2d] == 0:  # for each GPS profile only 1 count per vertical bin
                glb['nob'][location_2d] += 1.0
                single_profile[location_2d] += 1.0
            glb['cnt'][location_2d] += 1.0
            glb['fg_depar'][location_2d] += xiv
            glb['stdv_fg_depar'][location_2d] += xiv ** 2

            location_3d = (yidx, xidx, gps_index)

            glb['zonal_cnt'][location_3d] += 1.0
            glb['zonal_fg_depar'][location_3d] += xiv
            glb['zonal_stdv_fg_depar'][location_3d] += xiv ** 2

            if sens_on == True:
                ob_sens = np.float(nrl_data.at[row_number, 'OMF']) \
                          * np.float(nrl_data.at[row_number, 'SENS'])
                glb['sens_cnt'][location_2d] += 1.0
                glb['ob_sens'][location_2d] += ob_sens
                glb['zonal_sens_cnt'][location_3d] += 1.0
                glb['zonal_ob_sens'][location_3d] += ob_sens

        row_number += 1

    print('found ', data_count, '  GPS bending angle obs ')

    # compute the individual dtg means and standard deviations
    print('now computing the mean and standard deviation')
    good = np.where(glb['cnt'] > 0)
    good_zonal = np.where(glb['zonal_cnt'] > 0)

    no_good = np.where(glb['cnt'] == 0)
    no_good_zonal = np.where(glb['zonal_cnt'] == 0)

    glb['fg_depar'][good] = glb['fg_depar'][good] / glb['cnt'][good]
    glb['stdv_fg_depar'][good] = np.sqrt(glb['stdv_fg_depar'][good] / glb['cnt'][good] - glb['fg_depar'][good] ** 2)
    glb['zonal_fg_depar'][good_zonal] = glb['zonal_fg_depar'][good_zonal] / glb['zonal_cnt'][good_zonal]
    glb['zonal_stdv_fg_depar'][good_zonal] = np.sqrt(
        glb['zonal_stdv_fg_depar'][good_zonal] / glb['zonal_cnt'][good_zonal] - \
        glb['zonal_fg_depar'][good_zonal] ** 2)

    glb['fg_depar'][no_good] = MISSING
    glb['stdv_fg_depar'][no_good] = MISSING
    glb['zonal_fg_depar'][no_good_zonal] = MISSING
    glb['zonal_stdv_fg_depar'][no_good_zonal] = MISSING

    # print ' printing the means for latitude ', ly['bins'][10]
    # print ("%9.2f"*int(gps_types))%tuple(glb['fg_depar'][10,:])

    return glb, sens_on


def write_file(glb, output_path, output_file):
    """
    Write a file
    :param glb:
    :param output_path:
    :param output_file:
    :return:
    """
    print("Writing output file...  " + output_file)
    print('  ')
    print('  ')
    if os.path.exists(output_path) != True:
        os.mkdir(output_path)
    f = h5py.File(output_file, 'w')
    for k in glb:
        f.create_dataset(k, data=glb[k])
    f.close()


def time_window(number_of_days, dtg):
    """
    Time window
    :param number_of_days:
    :param dtg:
    :return:
    """
    #   create a list of date-time groups going back number_of_days at 6-hr intervals

    ncycles = 4 * int(number_of_days) + 1

    month = ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC']
    dom = np.array([31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31])

    print('Last ', number_of_days, ' Days of Data Assimilation cycles :)')

    iyyyy = int(dtg[0:4])
    imm = int(dtg[4:6])
    idd = int(dtg[6:8])
    ihh = int(dtg[8:10])

    if (iyyyy % 4) == 0:
        dom[1] = 29

    if (ihh % 6) != 0:
        print('only set for 6-hr intervals')

    my_index = []  # strarr(ncycles)
    dtg_index = []  # strarr(ncycles)

    for i in range(ncycles):
        if ihh < 0:
            ihh = 24 + ihh
            idd = idd - 1
            if idd <= 0:
                imm = imm - 1
                if imm <= 0:
                    iyyyy = iyyyy - 1
                    imm = 12
                    idd = 31
                else:
                    idd = dom[imm - 1]

        dtg_index.append("%.4i%.2i%.2i%.2i" % (iyyyy, imm, idd, ihh))
        my_index.append(month[imm - 1])

        ihh = ihh - 6

    dtg_index.reverse()
    my_index.reverse()

    return dtg_index, my_index


if __name__ == "__main__":

    from optparse import OptionParser

    usage = 'usage: %prog -d date-time -i input-loc -r ar_run [-s save-dir] [-n number_of_days]'

    parser = OptionParser(usage)
    parser.add_option('-i', '--input-loc', dest='filepath',
                      action='store', default=None,
                      help='Location of input files')
    parser.add_option('-d', '--date-time', dest='cdtg',
                      action='store', default=None,
                      help='10-digit date time group')
    parser.add_option('-n', '--number-of-days', dest='number_of_days',
                      action='store', default=30,
                      help='size of time window days backwards')
    parser.add_option('-s', '--save-dir', dest='output_dir',
                      action='store', default=None,
                      help='path where intermediary binary files will be written')
    parser.add_option('-r', '--run-name', dest='ar_run',
                      action='store', default=None,
                      help='name of experiment run')

    (options, args) = parser.parse_args()

    # chk date
    if options.cdtg:
        if len(options.cdtg) != 10:
            parser.error("expecting date in 10 character (yyyymmddhh) format \n \
                        received date: %s" % options.cdtg)
    else:
        parser.error("provide date in 10 character (yyyymmddhh) format, specify with -d option")

    if not options.filepath:
        parser.error("no path to monitoring directories given, specify with -i option")
    if not os.path.isdir(options.filepath):
        parser.error("Missing monitoring directory: %s" % options.filepath)

    if not options.output_dir:
        output_dir = options.filepath
    else:
        output_dir = options.output_dir

    if not options.ar_run:
        parser.error("no name for experiment run given, specify with -r option")

    main(options.filepath, options.cdtg, options.number_of_days, output_dir)
