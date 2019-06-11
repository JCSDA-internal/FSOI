import boto3
import datetime as dt

date = dt.datetime(2019, 2, 21, 0, 0, 0)
end = dt.datetime(2019, 6, 4, 0, 0, 0)
one_day = dt.timedelta(1)

batch = boto3.client('batch')

while date <= end:
    date_str = str(date).replace('-', '').replace(' ', '').replace(':', '')[:10]
    print(date_str)
    batch.submit_job(
        jobName='gmao_%s' % date_str,
        jobDefinition='ios_ingest_gmao_job:5',
        jobQueue='ios_ingest_queue',
        containerOverrides={
            'command': ['process_gmao', '-d', date_str]
        }
    )

    date = date + one_day
