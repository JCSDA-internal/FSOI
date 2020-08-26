import boto3
import datetime as dt

start = dt.datetime(2020, 6, 1, 0, 0, 0)
# end = dt.datetime(2020, 4, 1, 0, 0, 0)
end = dt.datetime(2020, 6, 30, 18, 0, 0)
one_day = dt.timedelta(hours=6)


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
        jobName='met_%s' % date_str,
        jobDefinition='ios_ingest_nrl_job:%d' % latest,
        jobQueue='ios_ingest_queue',
        containerOverrides={
            'command': ['process_met', '-o', '/tmp', '-d', date_str]  #, '-n', 'moist']
        }
    )


def submit_download_job_for_date(date):
    """
    Submit a job for a single date
    :param date: {str} Date/time string to download in the format YYYYMMDDHH
    :return: None
    """
    print('Submitting batch job to download NRL for: %s' % date)

    # submit the job
    batch = boto3.client('batch')
    latest = get_latest_revision('ios_ingest_nrl_job')
    batch.submit_job(
        jobName='nrl_%s' % date,
        jobDefinition='ios_ingest_nrl_job:%d' % latest,
        jobQueue='ios_ingest_queue',
        containerOverrides={
            'command': ['download_met', '--date', date]
        }
    )


if __name__ == '__main__':
    submit_jobs_in_range()
