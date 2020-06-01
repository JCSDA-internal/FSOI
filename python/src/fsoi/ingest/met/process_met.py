import os
import gzip
import yaml
import pkgutil
import tempfile
import numpy as np
import boto3
from datetime import datetime
from fortranformat import FortranRecordReader
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
from fsoi.stats import lib_utils as lutils
from fsoi.stats import lib_obimpact as loi
from fsoi import log
from fsoi.data.s3_datastore import FsoiS3DataStore, S3DataStore
from fsoi.data.datastore import ThreadedDataStore


def _parse_line(config, line, reader, unknown_platforms):
    """
    Parse a single line from the data file
    :param config: {dict} The UK Met configuration read from met_ingest.yaml
    :param line: {str|bytes} The line from the data file
    :param reader: {FortranRecordReader} Object to parse the line
    :param unknown_platforms: {list} List to store unknown platforms
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
    platform, channel = _get_platform_channel(config, obtyp, schar, instyp, unknown_platforms)

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


def _get_platform_channel(config, obtyp, schar, instyp, unknown_platforms):
    """
    Get a platform and channel
    :param config: {dict} The MET configuration read from met_ingest.yaml
    :param obtyp: {int} The observation type
    :param schar: {str} Not really sure what 'schar' means
    :param instyp: {int} Not really sure what 'instyp' means
    :param unknown_platforms: {list} List to store unknown platforms
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

    unknown_platforms.append('instyp: %s; schar: %s' % (instyp, schar))

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
    # get the configuration
    config = yaml.full_load(pkgutil.get_data('fsoi', 'ingest/met/met_ingest.yaml'))

    # parse the command line parameters
    parser = ArgumentParser(description='Process UKMet file', formatter_class=ArgumentDefaultsHelpFormatter)
    parser.add_argument('-i', '--input-file', help='Raw UKMet file', type=str, required=False)
    parser.add_argument('-o', '--output-path', help='Output path for the created files', type=str, required=True)
    parser.add_argument('-d', '--date', help='analysis date to process', metavar='YYYYMMDDHH', required=True)
    args = parser.parse_args()

    # store the command line parameters
    input_file = args.input_file
    output_path = args.output_path
    date_str = args.date
    date = datetime.strptime(date_str, '%Y%m%d%H')

    # do not delete an input file by default
    remove_input_file = False

    # if an input file was not specified, try to download one from S3 using the provided date
    if input_file is None:
        input_file = tempfile.mktemp()
        log.debug('Downloading input from S3 to %s' % input_file)
        datastore = S3DataStore()
        source = {'bucket': config['raw_data_bucket'], 'key': '%sT%s00Z.FSO.gz' % (date_str[:8], date_str[8:])}
        remove_input_file = datastore.load_to_local_file(source, input_file)

    # make sure we have an input file at this point
    if input_file is None or not os.path.isfile(input_file):
        log.error('Input data not available')
        return

    process_met(input_file, output_path, date, date_str)

    # maybe remove the input file
    if remove_input_file:
        print(input_file)
        # os.remove(input_file)


def process_met(input_file, output_path, date, date_str):
    """
    Process a raw NRL file
    :param input_file: {str} Full path to a raw NRL gzip file
    :param output_path: {str} Full path to the output directory
    :param date: {datetime} A localized to UTC datetime object
    :param date_str: {str} A datetime string in the format YYYYMMDDHH
    :return: {list} A list of output files, or None
    """
    # client to notify SNS topic if there are unknown platforms
    sns = boto3.client("sns")

    # list saving unknown platforms IDs
    unknown_platforms = []

    # read the MET config file
    config = yaml.full_load(pkgutil.get_data('fsoi', 'ingest/met/met_ingest.yaml'))

    # pylint wrongly believes that the FortranRecordReader constructor is not callable
    # pylint: disable=E1102
    reader = FortranRecordReader(config['fortran_format_string'])

    # process each line in the file
    # read the lines from the data file
    fh = gzip.open(input_file, 'rb')
    bufr = []
    nobs = 0
    while True:
        try:
            line = fh.readline()
            if line == b'':
                break
        except Exception as e:
            log.warn('Unexpected end of file after %d lines read' % nobs)
            log.warn(e)
            break

        # parse a single line and increase the observation count
        data = None
        try:
            data = _parse_line(config, line, reader, unknown_platforms)
        except Exception:
            log.warn('Failed to parse line: %s' % line)

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
    os.makedirs(output_path, exist_ok=True)
    datastore = ThreadedDataStore(FsoiS3DataStore(), thread_pool_size=4)
    output_file = 'MET.moist.%s.h5' % date_str
    if bufr:
        df = loi.list_to_dataframe(date, bufr)
        local_file = '%s/%s' % (output_path, output_file)
        lutils.writeHDF(local_file, 'df', df, complevel=1, complib='zlib', fletcher32=True)
        descriptor = FsoiS3DataStore.create_descriptor(center='MET', norm='moist', datetime=date_str)
        datastore.save_from_local_file(local_file, descriptor)

        df = loi.BulkStats(df)
        local_file = '%s/bulk.%s' % (output_path, output_file)
        lutils.writeHDF(local_file, 'df', df)
        descriptor = FsoiS3DataStore.create_descriptor(center='MET', norm='moist', datetime=date_str, type='bulk')
        datastore.save_from_local_file(local_file, descriptor)

        df = loi.accumBulkStats(df)
        local_file = '%s/accumbulk.%s' % (output_path, output_file)
        lutils.writeHDF('%s/accumbulk.%s' % (output_path, output_file), 'df', df)
        descriptor = FsoiS3DataStore.create_descriptor(center='MET', norm='moist', datetime=date_str, type='accumbulk')
        datastore.save_from_local_file(local_file, descriptor)

        platforms = loi.Platforms('OnePlatform')
        df = loi.groupBulkStats(df, platforms)
        local_file = '%s/groupbulk.%s' % (output_path, output_file)
        lutils.writeHDF('%s/groupbulk.%s' % (output_path, output_file), 'df', df)
        descriptor = FsoiS3DataStore.create_descriptor(center='MET', norm='moist', datetime=date_str, type='groupbulk')
        datastore.save_from_local_file(local_file, descriptor)

    # wait here for uploads to finish
    datastore.join()

    # check for errors saving data to S3
    for operation in datastore.operations:
        if not operation.success:
            log.debug('Failed to save file to S3: %s' % operation.parameters[0])

    # log a summary
    log.debug('Total obs = %d' % nobs)

    if unknown_platforms:
        unknown_platforms = list(set(unknown_platforms))
        sns.publish(
            TopicArn=config['arnUnknownPlatformsTopic'],
            Subject='Unknown Platform attribute UK Met file',
            Message='Unknown platform attribute encountered while processing files from UK Met. Unknown ID(s): ' +
                    ', '.join(str(e) for e in unknown_platforms) + ', file timestamp : ' + date_str
        )



if __name__ == '__main__':
    main()
