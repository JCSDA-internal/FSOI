#! /bin/sh

zip_file=fsoi-request-handler-deployed-`date +%Y%m%d%H%M%S`.zip
cd x
cp ../FSOI/scripts/lambda_wrapper.py .
cp ../FSOI/scripts/serverless_tools.py .
cp ../FSOI/scripts/ingest_navy.py .
cp ../FSOI/scripts/ingest_gmao.py .
zip -r ../$zip_file lambda_wrapper.py serverless_tools.py ingest_navy.py ingest_gmao.py chardet requests urllib3 certifi idna
cd ../

aws s3 cp $zip_file s3://jcsda-scratch/fsoi_lambda.zip
aws s3 cp $zip_file s3://jcsda-scratch/$zip_file
echo aws lambda update-function-code --function-name fsoi_request_handler --zip-file fileb://$zip_file
echo aws lambda update-function-code --function-name fsoi_ingest_nrl --zip-file fileb://$zip_file
echo aws lambda update-function-code --function-name fsoi_ingest_gmao --zip-file fileb://$zip_file
