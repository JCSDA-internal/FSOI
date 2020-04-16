import boto3
from logging import Handler
from logging import LogRecord
from datetime import datetime


class CloudWatchHandler(Handler):
    """
    A logging Handler class implementation that will log records to CloudWatch Logs in AWS
    """
    def __init__(self, log_group: str, log_stream: str):
        """
        Construct the CloudWatch handler
        :param log_group: The name of the CloudWatch log group
        :param log_stream: The name of the CloudWatch log stream
        """
        super().__init__()
        self.log_group = log_group
        self.log_stream = log_stream
        self.log_client = boto3.client('logs')
        self.sequence_token = None

    def emit(self, record: LogRecord):
        """
        Send the record to CloudWatch Logs
        :param record: The information to log
        :return: None
        """
        # make sure we have a sequence token to provide
        if self.sequence_token is None:
            self._get_sequence_token()

        try:
            # send the log event
            res = self.log_client.put_log_events(
                logGroupName=self.log_group,
                logStreamName=self.log_stream,
                logEvents=[CloudWatchHandler._record_to_log_event(record)],
                sequenceToken=self.sequence_token
            )

            # store the next sequence token
            self.sequence_token = res['nextSequenceToken']

            return
        except Exception as e:
            print(e)

        # logging action failed, try to get the next sequence token
        self._get_sequence_token()


    @staticmethod
    def _record_to_log_event(record: LogRecord):
        """
        Convert the record to a log event recognized by CloudWatch Logs:
        https://boto3.amazonaws.com/v1/documentation/api/1.11.5/reference/services/logs.html#CloudWatchLogs.Client.put_log_events
        :param record: The information to convert
        :return: {dict} A dictionary with timestamp and message elements
        """
        return {
            'timestamp': int(datetime.now().timestamp() * 1000),
            'message': '%s:%d  - %s' % (record.filename, record.lineno, record.getMessage())
        }

    def _get_sequence_token(self):
        """
        Get the next sequence token from CloudWatch
        :return: None
        """
        # query the CloudWatch service
        res = self.log_client.describe_log_streams(
            logGroupName=self.log_group,
            logStreamNamePrefix=self.log_stream,
            limit=1
        )

        # store the upload sequence token in this object
        self.sequence_token = res['logStreams'][0]['uploadSequenceToken']


def enable_cloudwatch_logs(turn_on_cloudwatch_logs: bool):
    """
    Enable or disable FSOI logging to CloudWatch Logs
    :param turn_on_cloudwatch_logs: Enable CloudWatch Logs if True, otherwise disable CloudWatch Logs
    :return: None
    """
    from fsoi import log

    cloudwatch_handlers = []
    for handler in log.handlers:
        if handler.__class__.__name__ == CloudWatchHandler.__class__.__name__:
            cloudwatch_handlers.append(handler)

    if turn_on_cloudwatch_logs:
        if len(cloudwatch_handlers) == 0:
            log.addHandler(CloudWatchHandler('fsoi_ingest', 'ingest_nrl'))
    else:
        for cwh in cloudwatch_handlers:
            log.removeHandler(cwh)
