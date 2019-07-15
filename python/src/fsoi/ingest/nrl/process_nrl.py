import os
import bz2
import pkgutil
import yaml
import boto3
import shutil
import fsoi.stats.lib_utils as lutils
import fsoi.stats.lib_obimpact as loi
from datetime import datetime
from fortranformat import FortranRecordReader
from fsoi import log


def _parse_line(line, kt, kx, fortran_format, uknownplats):
    """
    :param line:
    :param kt:
    :param kx:
    :param fortran_format: The fortran format of the line parameter
    :param uknownplats: List saving unknown platform IDs
    :return:
    """
    # pylint wrongly believes that the FortranRecordReader constructor is not callable
    # pylint: disable=E1102
    line_reader = FortranRecordReader(fortran_format)
    datain = line_reader.read(line)

    ob = datain[1]
    omf = datain[4]
    oberr = datain[5]
    lat = datain[7]
    lon = datain[8]
    lev = datain[9]
    obtyp = datain[10]
    instyp = datain[11]
    irflag = datain[13]
    schar = str(datain[15]) + '  ' + str(datain[16])
    num_reject = datain[19]
    resid = datain[22]
    sens = datain[23]

    impact = omf * sens

    if _skip_ob(instyp, impact):
        return None

    platform, channel = _get_platform_channel(instyp, schar, kx, uknownplats)

    dataout = {
        'platform': platform,
        'channel': channel,
        'obtype': kt[obtyp][0],
        'lat': lat,
        'lon': lon,
        'lev': lev,
        'impact': impact,
        'omf': omf,
        'ob': ob,
        'oberr': oberr,
        'oma': resid
    }

    return dataout


def _skip_ob(instyp, impact):
    """
    :param instyp:
    :param impact:
    :return:
    """
    # discard observations with very large observation error
    # if oberr > 1000.:
    #    return True

    # discard rejected observations
    # if num_reject != 0:
    #    return True

    # discard [land_surface,ship] obs with zero impact
    if instyp in [1, 10]:
        if impact == 0.:
            return True

    return False


def _get_platform_channel(instyp, schar, kx, uknownplats):
    """

    :param instyp:
    :param schar:
    :param kx:
    :param uknownplats: List saving unknown platform IDs
    :return:
    """
    channel = -999
    platform = 'unknown'

    schar = schar.upper()

    try:
        platform = kx[instyp]
    except KeyError as e:
        if int(e.args[0]) not in uknownplats:
            uknownplats.append(int(e.args[0]))
        return platform, channel

    if instyp in [10]:
        if 'BUOY' in schar:
            platform = 'Moored_Buoy'
        elif 'DRIFTER' in schar:
            platform = 'Drifting_Buoy'
        else:
            platform = 'Ship'

    elif instyp in [60]:
        if '13' in schar:
            platform = 'SSMI_13'
        elif '14' in schar:
            platform = 'SSMI_14'
        elif '15' in schar:
            platform = 'SSMI_15'

    elif instyp in [101]:
        if 'RECO' in schar:
            platform = 'Dropsonde'
        elif 'PIBAL' in schar:
            platform = 'PIBAL'
        else:
            platform = 'Radiosonde'

    #   elif instyp in [50,51,52,53,54,55,56,57,58,59,65,66]:
    #       platform = 'Sat_Wind'
    #       if 'MET9' in schar:
    #           platform = 'MET9'

    if platform in ['AMSUA']:
        if 'NOAA15' in schar:
            platform = '%s_N15' % platform
        elif 'NOAA16' in schar:
            platform = '%s_N16' % platform
        elif 'NOAA18' in schar:
            platform = '%s_N18' % platform
        elif 'NOAA19' in schar:
            platform = '%s_N19' % platform
        elif 'METOPA' in schar:
            platform = '%s_METOP-A' % platform
        elif 'METOPB' in schar:
            platform = '%s_METOP-B' % platform

        ichan = 0
        chanmin, chanmax = 1, 16
        for ichan in range(chanmin, chanmax):
            if 'CH%2s' % ichan in schar:
                break
        if ichan != chanmax:
            channel = ichan

    elif platform in ['IASI']:
        if 'METOPA' in schar:
            platform = '%s_METOP-A' % platform
        elif 'METOPB' in schar:
            platform = '%s_METOP-B' % platform

        ichan = 0
        chanmin, chanmax = 51, 412
        for ichan in range(chanmin, chanmax):
            if 'CH%4s' % ichan in schar:
                break
        if ichan != chanmax:
            channel = ichan

    elif platform in ['CrIS']:
        platform = '%s_NPP' % platform
        ichan = 0
        chanmin, chanmax = 1, 1143
        for ichan in range(chanmin, chanmax):
            if 'CH%5s' % ichan in schar:
                break
        if ichan != chanmax:
            channel = ichan

    elif platform in ['ATMS']:
        platform = '%s_NPP' % platform
        ichan = 0
        chanmin, chanmax = 1, 23
        for ichan in range(chanmin, chanmax):
            if 'CH%5s' % ichan in schar:
                break
        if ichan != chanmax:
            channel = ichan

    elif platform in ['MHS']:
        if 'NOAA18' in schar:
            platform = '%s_N18' % platform
        elif 'NOAA19' in schar:
            platform = '%s_N19' % platform
        elif 'METOPA' in schar:
            platform = '%s_METOP-A' % platform
        elif 'METOPB' in schar:
            platform = '%s_METOP-B' % platform

        ichan = 0
        chanmin, chanmax = 4, 6
        for ichan in range(chanmin, chanmax):
            if 'CH%5s' % ichan in schar:
                break
        if ichan != chanmax:
            channel = ichan

    elif platform in ['SSMIS']:
        ichan = 0
        chanmin, chanmax = 2, 25
        for ichan in range(chanmin, chanmax):
            if 'CH%3s' % ichan in schar:
                break
        if ichan != chanmax:
            channel = ichan

    return platform, channel


def process_nrl(raw_bzip2_file, output_path, output_file, date):
    """
    Process a raw NRL file
    :param raw_bzip2_file: {str} Full path to a raw NRL gzip file
    :param output_path: {str} Full path to the output directory
    :param output_file: {str} Output file name only (will also create files with some prefixes)
    :param date: {str} Date and time string in the format YYYYMMDDHH
    :return: {list} A list of output files, or None
    """

    sns = boto3.client("sns")

    #list saving unknown platforms IDs
    uknownplats = []

    parsed_date = datetime.strptime(date, '%Y%m%d%H')

    # open the raw data file
    try:
        fh = bz2.BZ2File(raw_bzip2_file, 'rb')
    except RuntimeError as e:
        log.error('Failed to open file: %s' % raw_bzip2_file)
        return None

    # skip the first 75 lines
    for _ in range(75):
        fh.readline()

    # read the remaining lines and close the file
    lines = fh.readlines()
    fh.close()

    # load constant values from a resources file
    config = yaml.full_load(pkgutil.get_data('fsoi', 'ingest/nrl/nrl_ingest.yaml'))
    fortran_format = config['fortran_format_string']
    kt = config['kt']
    kx = config['kx']

    # process each line
    line_number = 75
    n_obs = 0
    bufr = []

    for line in lines:

        line_number += 1

        # convert any byte array to a string
        if isinstance(line, bytes):
            line = line.decode()

        data = _parse_line(line, kt, kx, fortran_format, uknownplats)

        if data is None:
            continue

        n_obs += 1

        plat = data['platform']
        channel = data['channel']
        obtype = data['obtype']
        lon = data['lon'] if data['lon'] >= 0.0 else data['lon'] + 360.0
        lat = data['lat']
        lev = data['lev']
        imp = data['impact']
        omf = data['omf']
        oberr = data['oberr']

        line = [plat, obtype, channel, lon, lat, lev, imp, omf, oberr]

        bufr.append(line)

    # write a file if bufr is not empty
    output_files = []
    if bufr:
        out = '%s/%s' % (output_path, output_file)
        df = loi.list_to_dataframe(parsed_date, bufr)
        if os.path.isfile(out): os.remove(out)
        lutils.writeHDF(out, 'df', df, complevel=1, complib='zlib', fletcher32=True)
        output_files.append(out)

        df = loi.BulkStats(df)
        lutils.writeHDF('%s/bulk.%s' % (output_path, output_file), 'df', df)
        output_files.append('%s/bulk.%s' % (output_path, output_file))

        df = loi.accumBulkStats(df)
        lutils.writeHDF('%s/accumbulk.%s' % (output_path, output_file), 'df', df)
        output_files.append('%s/accumbulk.%s' % (output_path, output_file))

        platforms = loi.Platforms('OnePlatform')
        df = loi.groupBulkStats(df, platforms)
        lutils.writeHDF('%s/groupbulk.%s' % (output_path, output_file), 'df', df)
        output_files.append('%s/groupbulk.%s' % (output_path, output_file))

    else:
        return None

    log.debug('Total obs = %d' % n_obs)

    if uknownplats:
        sns.publish(
            TopicArn=config['arnUnknownPlatformsTopic'],
            Subject='Unknown Platform attribute NRL file',
            Message='Unknown platform attribute encountered while processing files from NRL. Unknown platform ID(s): ' + ', '.join(str(e) for e in uknownplats) + ', file timestamp : ' + date
        )
    return output_files


def main():
    """
    Parse command line parameters and run the process_nrl function
    :return: None
    """

    from argparse import ArgumentParser
    from argparse import ArgumentDefaultsHelpFormatter

    # setup the argument parser
    parser = ArgumentParser(description='Process NRL file',
                            formatter_class=ArgumentDefaultsHelpFormatter)
    parser.add_argument('-d', '--date', help='analysis date to process', metavar='YYYYMMDDHH',
                        required=True)
    args = parser.parse_args()
    
    # prepare the working directory
    # prepare the processing parameters
    date = args.date

    work_dir = '/tmp/work/nrl/%s' % date
    os.makedirs(work_dir, exist_ok=True)
    os.chdir(work_dir)
    input_file = download_from_s3('s3://fsoi-navy-ingest/obimpact_gemops_%s.bz2' % date)
    output_file = 'NRL.dry.%s.h5' % date

    # process the data
    output_files = process_nrl(input_file, work_dir, output_file, date)
    if not output_files:
        log.error('Error processing file: %s' % input_file)
    else:
        log.info('Uploading files to S3:')
        for file in output_files:
            s3url = 's3://fsoi/intercomp/hdf5/NRL/%s' % file.split('/')[-1]
            print('%s -> %s' % (file, s3url))
            uploaded = upload_to_s3(file, s3url)
            if not uploaded:
                print('Failed to upload %s to %s' % (file, s3url))


def prepare_workspace():
    """
    Prepare workspace
    :return: {str} Full path to the workspace, or None if could not create
    """
    try:
        work_dir = '/tmp/work'
        if os.path.exists(work_dir):
            shutil.rmtree(work_dir)
        os.makedirs(work_dir)
        return work_dir
    except Exception as e:
        print('Failed to create workspace: /tmp/work')
        print(e)
        return None


def download_from_s3(s3url):
    """
    Download a BZ2 object from S3 and uncompress it
    :param s3url: {str} The S3 URL
    :return: {str}
    """
    # create an s3 client
    s3 = boto3.client('s3')

    # parse a few things from the url
    file_name = s3url.split('/')[-1]
    bucket = s3url.split('/')[2]
    key = s3url.split(bucket + '/')[1]

    # download the data object from S3 to a file
    with open(file_name, 'wb') as file:
        s3.download_fileobj(bucket, key, file)
        file.close()

    return file_name


def upload_to_s3(file, s3url):
    """
    Upload a file to S3
    :param file: Path to the local file
    :param s3url: An S3 URL for the target
    :return: True if successful, otherwise false
    """
    try:
        # create an s3 client
        s3 = boto3.client('s3')

        # parse a few things from the url
        bucket = s3url.split('/')[2]
        key = s3url.split(bucket + '/')[1]

        # upload the file to the S3 bucket
        with open(file, 'rb') as file:
            s3.upload_fileobj(file, bucket, key)
        return True

    except Exception as e:
        log.error('Failed to upload file to S3: %s to %s' % (file, s3url))
        log.error(e)
        return False
