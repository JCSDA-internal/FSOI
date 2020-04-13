#! /bin/sh

# get the correct readlink executable
readlink=greadlink
if [[ $(uname -s) == "Linux" ]]; then
  readlink=readlink
fi

# get the root directory of the git repo
root_dir=$(${readlink} -f $(dirname $0)/..)

# set the zip file location
zip_dir=$(${readlink} -f "${root_dir}/../")
zip_file="fsoi-request-handler-deployed-`date +%Y%m%d%H%M%S`.zip"

# package the python code
cd ${root_dir}/python/src

# link to the lambda wrapper, which must be at the root level
ln -s ${root_dir}/python/src/fsoi/web/lambda_wrapper.py .

# set the permissions correctly before making the zip file
find . -type f -name \*.py -exec chmod ugo+rx {} \;
find . -type f -exec chmod ugo+r {} \;
find . -type d -exec chmod ugo+rx {} \;

# make the zip file
zip -r ${zip_dir}/${zip_file} lambda_wrapper.py fsoi
echo "Created zip file at ${zip_dir}/${zip_file}"

# copy the zip file to S3
aws s3 cp ${zip_dir}/${zip_file} s3://jcsda-scratch/fsoi_lambda.zip
aws s3 cp ${zip_dir}/${zip_file} s3://jcsda-scratch/${zip_file}

# print the command to update the lambda function code
echo aws lambda update-function-code --function-name ios_request_handlerbeta --s3-bucket jcsda-scratch --s3-key ${zip_file}
