import boto3
import json
from datetime import datetime

if __name__ == '__main__':
    log_group = 'fsoi_ingest'
    log_stream = 'ingest_nrl'

    # get the logs client
    log_client = boto3.client('logs')

    # get the upload sequence token
    res = log_client.describe_log_streams(
        logGroupName=log_group,
        logStreamNamePrefix=log_stream,
        limit=1
    )
    sequence_token = res['logStreams'][0]['uploadSequenceToken']

    # send the log event
    res = log_client.put_log_events(
        logGroupName=log_group,
        logStreamName=log_stream,
        logEvents=[{'timestamp': int(datetime.now().timestamp()), 'message': 'Test message'}],
        sequenceToken=sequence_token
    )
    print(json.dumps(res, indent='  '))
    sequence_token = res['nextSequenceToken']
