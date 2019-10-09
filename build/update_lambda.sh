#! /bin/sh

zip_file=fsoi-request-handler-deployed-`date +%Y%m%d%H%M%S`.zip
mkdir -p x
cd x
cp -R ../FSOI/python/src/fsoi .
rm -f ingest_navy.py ingest_gmao.py lambda_wrapper.py
#pip3 install -t . chardet requests urllib3 certifi idna pandas python-dateutil pytz six pyyaml matplotlib pyparsing cycler kiwisolver mpltools setuptools numexpr mock tables
ln -s fsoi/ingest/nrl/ingest_navy.py .
ln -s fsoi/ingest/gmao/ingest_gmao.py .
ln -s fsoi/web/lambda_wrapper.py .
find . -type f -name \*.py -exec chmod ugo+rx {} \;
find . -type f -exec chmod ugo+r {} \;
find . -type d -exec chmod ugo+rx {} \;
zip -r ../$zip_file ingest_navy.py ingest_gmao.py lambda_wrapper.py fsoi chardet requests urllib3 certifi idna pandas dateutil pytz six.py yaml matplotlib pyparsing.py cycler.py kiwisolver.cpython-37m-x86_64-linux-gnu.so mpl_toolkits pkg_resources numexpr mock tables

cd ../

aws s3 cp $zip_file s3://jcsda-scratch/fsoi_lambda.zip
aws s3 cp $zip_file s3://jcsda-scratch/$zip_file
echo aws lambda update-function-code --function-name ios_request_handler --s3-bucket jcsda-scratch --s3-key $zip_file
echo aws lambda update-function-code --function-name fsoi_ingest_nrl --zip-file fileb://$zip_file
echo aws lambda update-function-code --function-name fsoi_ingest_gmao --zip-file fileb://$zip_file
