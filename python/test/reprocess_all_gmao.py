import boto3
import datetime as dt
from fsoi.ingest import compute_lag_from_date

start = dt.datetime(2020, 7, 23, 0, 0, 0)
end = dt.datetime(2020, 9, 15, 0, 0, 0)
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
        # submit_download_job_for_date(date)
        submit_process_job_for_date(date_str)
        date = date + one_day


def submit_process_job_for_date(date_str):
    """
    Submit a job for a single date
    :param date_str: {str} YYYYMMDDHH
    :return: None
    """
    print('Submitting batch job to process GMAO for: %s' % date_str)

    batch = boto3.client('batch')

    lag = compute_lag_from_date(date_str)

    latest = get_latest_revision('ios_ingest_gmao_job')
    batch.submit_job(
        jobName='process_gmao_%s' % date_str,
        jobDefinition='ios_ingest_gmao_job:%d' % latest,
        jobQueue='ios_ingest_queue',
        containerOverrides={
            'command': ['ingest_gmao', '--lag', str(lag), '--norm', 'moist']
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
    print('Submitting batch job to ingest GMAO for: %s, %d days ago' % (date_str, lag))

    # submit the job
    batch = boto3.client('batch')
    latest = get_latest_revision('ios_ingest_gmao_job')
    batch.submit_job(
        jobName='download_gmao_%s' % date_str,
        jobDefinition='ios_ingest_gmao_job:%d' % latest,
        jobQueue='ios_ingest_queue',
        containerOverrides={
            'command': ['download_gmao', '--lag', str(lag)]
        }
    )


if __name__ == '__main__':
    submit_jobs_in_range()
