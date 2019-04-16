"""
Regression test for the process_NRL.py script
"""


def test_process_sample_nrl_file():
    """
    This test will download a sample file from S3 and process the file, then compute the SHA-256
    checksum of the output file to a known good checksum.  If the checksums match, the test passes.
    :return: None
    """
    import sys
    import os
    import boto3
    import bz2
    import gzip
    import hashlib
    from process_NRL import main as process_nrl_main

    # get an S3 client
    s3 = boto3.client('s3')

    # parameters
    bucket = 'fsoi-navy-ingest'
    date = '2019020800'
    key = 'obimpact_gemops_%s.bz2' % date
    bzip_file = '/tmp/nrl_sample.bz2'
    gzip_file = '/tmp/nrl_sample.gz'
    output_file = '/tmp/nrl_processed'

    # download the sample data from S3
    with open(bzip_file, 'wb') as file:
        s3.download_fileobj(bucket, key, file)
        file.close()

    # convert bz2 to gz
    with gzip.open(gzip_file, 'wb') as out, bz2.BZ2File(bzip_file, 'rb') as inp:
        for data in iter(lambda: inp.read(102400), b''):
            out.write(data)
        out.close()

    # process the gzip file
    sys.argv = ('script -i %s -o %s -a %s' % (gzip_file, output_file, date)).split()
    process_nrl_main()

    # compute the hash on the output file
    sha = hashlib.sha256()
    with open(output_file, 'rb') as file:
        for chunk in iter(lambda: file.read(65536), b''):
            sha.update(chunk)

    # compare the checksum to a known good checksum
    chksum = sha.hexdigest()
    assert chksum == '23d0899af8a7996627657a35843d490e42e03543468364886a1ca942dcbda3bf'

    # clean up
    os.remove(output_file)
    os.remove(bzip_file)
    os.remove(gzip_file)
