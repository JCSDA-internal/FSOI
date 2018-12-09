#! /bin/sh

zip_file=../fsoi-lambda-deployed-`date +%Y%m%d%H%M%S`.zip
cd x
cp ../FSOI/scripts/lambda_wrapper.py .
zip -r $zip_file .

aws lambda update-function-code --function-name gen_fsoi_chart --zip-file fileb://$zip_file
