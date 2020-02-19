import gzip
import yaml
import pkgutil
import numpy as np
from datetime import datetime
from fortranformat import FortranRecordReader
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
from fsoi.stats import lib_utils as lutils
from fsoi.stats import lib_obimpact as loi
from fsoi import log
from fsoi.data.s3_datastore import FsoiS3DataStore
from fsoi.data.datastore import ThreadedDataStore


def _parse_line(config, line, reader):
    """
    Parse a single line from the data file
    :param config: {dict} The UK Met configuration read from met_ingest.yaml
    :param line: {str|bytes} The line from the data file
    :param reader: {FortranRecordReader} Object to parse the line
    :return:
    """
    # extract data from the configuration
    kt = config['kt']

    # make sure we have a string and not a byte array
    if type(line) == bytes:
        line = line.decode()

    # parse the line
    datain = reader.read(line)

    # put the tokens into well-named variables
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

    # calculate the impact value
    impact = omf * sens

    # determine if this observation should be skipped
    if _skip_ob(impact):
        log.warning('SKIPPING : %s' % line.strip())
        return None

    # get the platform and channel for this observation
    platform, channel = _get_platform_channel(config, obtyp, schar, instyp)

    dataout = dict()
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


def _get_platform_channel(config, obtyp, schar, instyp):
    """
    Get a platform and channel
    :param config: {dict} The MET configuration read from met_ingest.yaml
    :param obtyp: {int} The observation type
    :param schar: {str} Not really sure what 'schar' means
    :param instyp: {int} Not really sure what 'instyp' means
    :return: {str, int} The platform name and channel
    """
    # initialize variables to not found
    schar = schar.upper()
    channel = -999

    platforms = config['platforms']

    # get the correct platform list base on the obtyp
    if obtyp in platforms['observation_types_for_radiance']:
        platforms = platforms['radiance']
        channel = int(schar.split()[-2].split('-')[-1])
        schar = schar.split('-')[0]
    else:
        platforms = platforms['conventional']

    # find the right platform name
    for platform in platforms:
        # some platforms require another level to match instyp value
        if type(platforms[platform][0]) == dict:
            for s in platforms[platform]:
                for partial_name in s:
                    if partial_name.upper() in schar:
                        if instyp in s[partial_name]:
                            platform = platform
                            return platform, channel
        else:
            for partial_name in platforms[platform]:
                if partial_name.upper() in schar:
                    platform = platform
                    return platform, channel

    return 'UNKNOWN', channel


def _skip_ob(impact):
    """
    Determine whether or not to skip this observation
    :param impact: {float} ???
    :return: True if this observation should be skipped
    """
    # discard obs with very large impact
    if np.abs(impact) > 1.e-3:
        return True

    return False


def main():
    """
    Process a specified file and output statistics, bulk statistics, accumbulk statistics, & group bulk statistics files
    :return: None
    """
    # parse the command line parameters
    parser = ArgumentParser(description='Process UKMet file', formatter_class=ArgumentDefaultsHelpFormatter)
    parser.add_argument('-i', '--input-file', help='Raw UKMet file', type=str, required=True)
    parser.add_argument('-o', '--output-path', help='Output path for the created files', type=str, required=True)
    parser.add_argument('-d', '--date', help='analysis date to process', metavar='YYYYMMDDHH', required=True)
    args = parser.parse_args()

    input_file = args.input_file
    output_path = args.output_path
    date = datetime.strptime(args.date, '%Y%m%d%H')

    # read the lines from the data file
    fh = gzip.open(input_file, 'rb')
    lines = fh.readlines()
    fh.close()

    # read the MET config file
    config = yaml.full_load(pkgutil.get_data('fsoi', 'ingest/met/met_ingest.yaml'))

    # pylint wrongly believes that the FortranRecordReader constructor is not callable
    # pylint: disable=E1102
    reader = FortranRecordReader(config['fortran_format_string'])

    # process each line in the file
    bufr = []
    nobs = 0
    for line in lines:
        # parse a single line and increase the observation count
        data = _parse_line(config, line, reader)
        if data is None:
            continue
        nobs += 1

        # extract the data from the parsed line
        plat = data['platform']
        channel = data['channel']
        obtype = data['obtype']
        lon = data['lon'] if data['lon'] >= 0.0 else data['lon'] + 360.0
        lat = data['lat']
        lev = data['lev']
        imp = data['impact']
        omf = data['omf']
        oberr = data['oberr']

        # reformat the data and add a new line
        line = [plat, obtype, channel, lon, lat, lev, imp, omf, oberr]
        bufr.append(line)

    # write the output files and upload to the S3 datastore
    datastore = ThreadedDataStore(FsoiS3DataStore(), thread_pool_size=4)
    output_file = 'MET.dry.%s.h5' % args.date
    if bufr:
        df = loi.list_to_dataframe(date, bufr)
        local_file = '%s/%s' % (output_path, output_file)
        lutils.writeHDF(local_file, 'df', df, complevel=1, complib='zlib', fletcher32=True)
        descriptor = FsoiS3DataStore.create_descriptor(center='MET', norm='dry', datetime=args.date)
        datastore.save_from_local_file(local_file, descriptor)

        df = loi.BulkStats(df)
        local_file = '%s/bulk.%s' % (output_path, output_file)
        lutils.writeHDF(local_file, 'df', df)
        descriptor = FsoiS3DataStore.create_descriptor(center='MET', norm='dry', datetime=args.date, type='bulk')
        datastore.save_from_local_file(local_file, descriptor)

        df = loi.accumBulkStats(df)
        local_file = '%s/accumbulk.%s' % (output_path, output_file)
        lutils.writeHDF('%s/accumbulk.%s' % (output_path, output_file), 'df', df)
        descriptor = FsoiS3DataStore.create_descriptor(center='MET', norm='dry', datetime=args.date, type='accumbulk')
        datastore.save_from_local_file(local_file, descriptor)

        platforms = loi.Platforms('OnePlatform')
        df = loi.groupBulkStats(df, platforms)
        local_file = '%s/groupbulk.%s' % (output_path, output_file)
        lutils.writeHDF('%s/groupbulk.%s' % (output_path, output_file), 'df', df)
        descriptor = FsoiS3DataStore.create_descriptor(center='MET', norm='dry', datetime=args.date, type='groupbulk')
        datastore.save_from_local_file(local_file, descriptor)

    # wait here for uploads to finish
    datastore.join()

    # check for errors saving data to S3
    for operation in datastore.operations:
        if not operation.success:
            log.debug('Failed to save file to S3: %s' % operation.parameters[0])

    # log a summary
    log.debug('Total obs = %d' % nobs)


if __name__ == '__main__':
    main()
