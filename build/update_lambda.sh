#! /bin/sh

zip_file=fsoi-request-handler-deployed-`date +%Y%m%d%H%M%S`.zip
cd x
cp -R ../FSOI/python/src/fsoi .
rm -f ingest_navy.py ingest_gmao.py lambda_wrapper.py
ln -s fsoi/ingest/nrl/ingest_navy.py .
ln -s fsoi/ingest/gmao/ingest_gmao.py .
ln -s fsoi/web/lambda_wrapper.py .
find . -type f -name \*.py -exec chmod ugo+rx {} \;
find . -type d -exec chmod ugo+rx {} \;
zip -r ../$zip_file ingest_navy.py ingest_gmao.py lambda_wrapper.py fsoi chardet requests urllib3 certifi idna
cd ../

aws s3 cp $zip_file s3://jcsda-scratch/fsoi_lambda.zip
aws s3 cp $zip_file s3://jcsda-scratch/$zip_file
echo aws lambda update-function-code --function-name fsoi_request_handler --zip-file fileb://$zip_file
echo aws lambda update-function-code --function-name fsoi_ingest_nrl --zip-file fileb://$zip_file
echo aws lambda update-function-code --function-name fsoi_ingest_gmao --zip-file fileb://$zip_file
