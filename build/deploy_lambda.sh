#! /bin/sh

zip_file=../handle-fsoi-request-deployed-`date +%Y%m%d%H%M%S`.zip
cd x
cp ../FSOI/scripts/lambda_wrapper.py .
cp ../FSOI/scripts/serverless_tools.py .
zip -r $zip_file lambda_wrapper.py serverless_tools.py chardet requests urllib3 certifi idna

aws lambda update-function-code --function-name handle_fsoi_request --zip-file fileb://$zip_file
