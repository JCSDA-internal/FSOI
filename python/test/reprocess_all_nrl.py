import boto3
import datetime as dt

start = dt.datetime(2020, 3, 22, 0, 0, 0)
end = dt.datetime(2020, 3, 27, 0, 0, 0)
one_day = dt.timedelta(1)


def get_latest_revision(job_definition_name):
    """
    Get the latest revision number of
    :param job_definition_name: {str} Job definition name
    :return: {int} The latest revision number
    """
    batch = boto3.client('batch')
    res = batch.describe_job_definitions(jobDefinitionName=job_definition_name)

    latest = -999
    for job_definition in res['jobDefinitions']:
        if job_definition['revision'] > latest:
            latest = job_definition['revision']

    if latest == -999:
        print('No job definition revision found')
        return None

    return latest


def submit_jobs_in_range():
    """
    Submit jobs in the date range set
    :return: None
    """
    date = start
    while date <= end:
        date_str = str(date).replace('-', '').replace(' ', '').replace(':', '')[:10]
        submit_job_for_date(date_str)
        date = date + one_day


def submit_job_for_date(date_str):
    """
    Submit a job for a single date
    :param date_str: {str} YYYYMMDDHH
    :return: None
    """
    print('Submitting batch job to process NRL for: %s' % date_str)

    batch = boto3.client('batch')

    latest = get_latest_revision('ios_ingest_nrl_job')
    batch.submit_job(
        jobName='nrl_%s' % date_str,
        jobDefinition='ios_ingest_nrl_job:%d' % latest,
        jobQueue='ios_ingest_queue',
        containerOverrides={
            'command': ['process_nrl', '-d', date_str]  #, '-n', 'moist']
        }
    )


def submit_download_job_for_date(date):
    """
    Submit a job for a single date
    :param date_str: {datetime} Valid time of data to download
    :return: None
    """
    now = dt.datetime.utcnow()
    date_str = str(date).replace('-', '').replace(' ', '').replace(':', '')[:10]
    lag = int((now - date).total_seconds() // 86400)
    print('Submitting batch job to download NRL for: %s, %d days ago' % (date_str, lag))

    # submit the job
    batch = boto3.client('batch')
    latest = get_latest_revision('ios_ingest_nrl_job')
    batch.submit_job(
        jobName='nrl_%s' % date_str,
        jobDefinition='ios_ingest_nrl_job:%d' % latest,
        jobQueue='ios_ingest_queue',
        containerOverrides={
            'command': ['download_nrl', '--lag', str(lag)]
        }
    )


if __name__ == '__main__':
    submit_jobs_in_range()
