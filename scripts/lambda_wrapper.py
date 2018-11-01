def lambda_gen_fsoi_chart(event, context):
    """
    Create a chart as a PNG based on the input parameters
    :param event: Contains the HTTP request
    :param context: Contains details of the lambda function
    :return: The HTTP response, including Base64-encoded PNG
    """
    qsp = event['queryStringParameters']

    s = 'start date: ' + qsp['startDate'] + '\n'
    s += 'end date  : ' + qsp['endDate'] + '\n'
    s += 'center    : ' + qsp['center'] + '\n'
    s += 'norm      : ' + qsp['norm'] + '\n'
    s += 'interval  : ' + qsp['interval'] + '\n'
    s += 'platforms : ' + str(qsp['platforms'].split(',')) + '\n'

    return create_response(s)


def create_response(body):
    """
    Create a successful response with the given body
    :param body: The body of the response message
    :return: An HTTP response message
    """
    import base64

    response = dict()
    response['isBase64Encoded'] = True
    response['headers'] = {}
    response['headers']['Content-Type'] = 'image/png'
    response['headers']['Content-Encoding'] = 'utf-8'
    response['headers']['Access-Control-Allow-Origin'] = '*'
    response['headers']['Access-Control-Allow-Credentials'] = True
    response['body'] = base64.b64encode(body.encode('utf-8')).decode('utf-8')

    return response
