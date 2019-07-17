import os
import yaml
import pkgutil
import shutil
import boto3
from datetime import datetime
from netCDF4 import Dataset
import numpy as np
from argparse import ArgumentParser
from argparse import ArgumentDefaultsHelpFormatter as FormatHelper
import fsoi.stats.lib_utils as lutils
import fsoi.stats.lib_obimpact as loi
from fsoi import log


class ODS:
    """
    ODS Class
    """

    def __init__(self, filename):
        """
        Constructor
        :param filename:
        """
        try:
            self.filename = filename
            self.file_ = Dataset(filename, 'r')
            self.file_.set_auto_mask(False)
            self.qcexcl = None
            self.xvec = []
            self.kx = []
            self.kt = []
            self.lev = []
            self.lon = []
            self.lat = []
            self.obs = []
            self.omf = []
            self.n_obs = 0
        except RuntimeError as e:
            raise IOError(str(e) + ' ' + filename)

    def read(self, only_good=True, platform=None):
        """

        :param only_good:
        :param platform:
        :return:
        """
        # pylint wrongly believes self.file_.variables is not iterable or subscriptable
        # pylint: disable=E1133, E1136
        for vname in self.file_.variables:
            if vname in ['days', 'syn_beg', 'syn_len']:
                continue
            tmp = self.file_.variables[vname][:]
            if vname in ['kt_names', 'kt_units', 'kx_names', 'kx_meta', 'qcx_names']:
                tmp2 = []
                for i in range(len(tmp)):
                    tmp2.append(self.__masked_array_to_str(tmp[i]))
                tmp = tmp2
            self.__setattr__(vname, tmp)

        if only_good:
            indx = self.qcexcl == 0
        else:
            indx = np.ma.logical_and(self.qcexcl >= 0, self.qcexcl <= 255)

        # Skip radiance observations that were rejected in 1st outer loop
        # but assimilated in the 2nd outer loop.
        # These observations are assigned ZERO impact value.
        # See email correspondence with Ron.Gelaro dated September 27, 2016
        if platform not in ['CONV']:
            indx = np.ma.logical_and(indx, np.abs(self.xvec) > 1.e-30)

        for name in ['lat', 'lon', 'lev', 'time', 'kt', 'kx', 'ks', 'xm', 'obs', 'omf', 'oma',
                     'xvec', 'qcexcl', 'qchist']:
            exec('self.%s = self.%s[indx]' % (name, name))

        self.n_obs = len(self.kx)

        return self

    @staticmethod
    def __masked_array_to_str(data):
        """
        Convert a {MaskedArray} to a {str}
        :param data: {MaskedArray} data
        :return: {str}
        """
        s = ''
        for c in data:
            s += bytes(c).decode()

        return s

    def close(self):
        """

        :return:
        """
        try:
            self.file_.close()
        except RuntimeError as e:
            raise IOError(str(e) + ' ' + self.filename)


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
        log.error('Failed to create workspace: /tmp/work')
        log.error(e)
        return None


def download_from_s3(s3url, local_dir):
    """
    Download all of the S3 objects with the given URL (bucket and prefix)
    :param s3url: {str} The S3 URL prefix
    :param local_dir: {str} Download data to this local directory
    :return: {list} A list of local files, or None if there was an error
    """
    # create an s3 client
    s3 = boto3.client('s3')

    # parse a few things from the url
    bucket = s3url.split('/')[2]
    prefix = s3url.split(bucket + '/')[1]

    # list the objects in the bucket at the prefix
    response = s3.list_objects(
        Bucket=bucket,
        Prefix=prefix
    )

    # check for an error response
    if response['ResponseMetadata']['HTTPStatusCode'] != 200:
        log.error('Error listing objects in bucket: %s' % s3url)
        return None

    # ensure the local directory exists
    os.makedirs(local_dir, exist_ok=True)

    # download each of the objects to a local file
    files = []
    for object_data in response['Contents']:
        # get the key and local file
        key = object_data['Key']
        local_file = key.split('/')[-1]
        full_local_file_path = '%s/%s' % (local_dir, local_file)

        # download the data object from S3 to a file
        with open(full_local_file_path, 'wb') as file:
            s3.download_fileobj(bucket, key, file)
            file.close()
            files.append(full_local_file_path)

    return files


def upload_to_s3(file, s3url):
    """
    Upload a file to S3
    :param file: Path to the local file
    :param s3url: An S3 URL for the target
    :return: True if successful, otherwise false
    """
    try:
        # log debug
        log.debug('Uploading %s to %s' % (file, s3url))

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
        return False


def process_gmao(norm, date):
    """
    Process the GMAO data from a given day for the specified norm
    :param norm: {str} moist or dry
    :param date: {str} Date string in the format YYYYMMDDHH
    :return: {list} List of local files
    """
    config = yaml.full_load(pkgutil.get_data('fsoi', 'ingest/gmao/gmao_ingest.yaml'))
    kx = config['kx']
    kt = config['kt']
    file_norm = config['norm'][norm]
    input_bucket = config['raw_data_bucket']
    dt = datetime.strptime(date, '%Y%m%d%H')

    work_dir = prepare_workspace()
    s3_prefix = 's3://%s/Y%s/M%s/D%s/H%s/' % (
        input_bucket, date[0:4], date[4:6], date[6:8], date[8:10])
    file_list = download_from_s3(s3_prefix, work_dir)

    n_obs = 0
    bufr = []
    # create list of unknown platforms
    ukwnplats = []

    for file in file_list:

        # skip if the norm is not in the file name
        if file_norm not in file.split('/')[-1]:
            continue

        # log debug
        log.debug('processing %s' % file)

        # TODO: Request that NASA adds the platform name as a global attribute in the NetCDF file
        #       rather than trying to parse the platform name from the file name.
        platform = file.split(
            '/')[-1].split('.')[3].split('imp3_%s_' % file_norm)[-1].upper()

        # read the data from the file
        ods = ODS(file)
        ods = ods.read(only_good=True, platform=platform)
        ods.close()

        # update the total obs count
        n_obs += ods.n_obs
        log.debug('platform = %s, nobs = %d' % (platform, ods.n_obs))

        # create client boto3 for unknown platform error raising
        sns = boto3.client("sns")

        # iterate over each observation
        for o in range(ods.n_obs):

            try:
                plat = kx[ods.kx[o]] if platform in ['CONV'] else platform
            except KeyError as e:
                platid = int(e.args[0])
                if platid not in ukwnplats:
                    ukwnplats.append(platid)

            obtype = kt[ods.kt[o]][0]

            channel = -999 if platform in ['CONV'] else np.int(ods.lev[o])
            lon = ods.lon[o] if ods.lon[o] >= 0.0 else ods.lon[o] + 360.0
            lat = ods.lat[o]
            if obtype == 'ps':
                lev = ods.obs[o]
            elif obtype == 'Tb':
                lev = -999.
            else:
                lev = ods.lev[o]
            imp = ods.xvec[o]
            omf = ods.omf[o]
            oberr = -999.  # GMAO does not provide obs error in the impact ODS files
            bufr.append([plat, obtype, channel, lon,
                         lat, lev, imp, omf, oberr])

    # send email if unknown platforms ID are encountered while processing GMAO files
    if ukwnplats :
        sns.publish(
            TopicArn=config['arnUnknownPlatformsTopic'],
            Subject='Unknown Platform attribute GMAO file',
            Message='Unknown platform attribute encountered while processing files from GMAO. Unknown platform ID(s): ' + ', '.join(str(e) for e in ukwnplats) + ', file timestamp : ' + date
        )

    log.debug('Total obs used in %s = %d' % (date, n_obs))

    # write the output files and upload to S3
    if not bufr:
        return None

    out_file_list = []

    out_file = 'GMAO.%s.%s.h5' % (norm, date)
    s3_template = 's3://fsoi/intercomp/hdf5/GMAO/%s'

    df = loi.list_to_dataframe(dt, bufr)
    of = '%s/%s' % (work_dir, out_file)
    lutils.writeHDF(of, 'df', df, complevel=1, complib='zlib', fletcher32=True)
    out_file_list.append(of)
    if not upload_to_s3(of, s3_template % of.split('/')[-1]):
        log.error('Failed to upload file to S3: %s' % of)

    df = loi.BulkStats(df)
    of = '%s/bulk.%s' % (work_dir, out_file)
    out_file_list.append(of)
    lutils.writeHDF(of, 'df', df)
    if not upload_to_s3(of, s3_template % of.split('/')[-1]):
        log.error('Failed to upload file to S3: %s' % of)

    df = loi.accumBulkStats(df)
    of = '%s/accumbulk.%s' % (work_dir, out_file)
    out_file_list.append(of)
    lutils.writeHDF(of, 'df', df)
    if not upload_to_s3(of, s3_template % of.split('/')[-1]):
        log.error('Failed to upload file to S3: %s' % of)

    platforms = loi.Platforms('OnePlatform')
    df = loi.groupBulkStats(df, platforms)
    of = '%s/groupbulk.%s' % (work_dir, out_file)
    out_file_list.append(of)
    lutils.writeHDF(of, 'df', df)
    if not upload_to_s3(of, s3_template % of.split('/')[-1]):
        log.error('Failed to upload file to S3: %s' % of)

    return out_file_list


def main():
    """

    :return:
    """
    parser = ArgumentParser(
        description='Process GMAO data', formatter_class=FormatHelper)
    parser.add_argument('-d', '--date', help='analysis date to process', metavar='YYYYMMDDHH',
                        required=True)
    parser.add_argument('-n', '--norm', help='norm to process', type=str, default='moist',
                        choices=['dry', 'moist'], required=False)
    args = parser.parse_args()

    files = process_gmao(args.norm, args.date)
    log.info('Processed GMAO files:')
    for file in files:
        log.info(file)


if __name__ == '__main__':
    main()
