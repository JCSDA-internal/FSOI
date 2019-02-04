#!/bin/bash

# This script does not execute anything for now, but shows steps to deploy the application

# 1. Create the docker image and push it to AWS ECR.  This image will process requests:
#   > docker build -t 469205354006.dkr.ecr.us-east-1.amazonaws.com/fsoi-batch .
#   > aws ecr get-login --no-include-email
#   The command above will generate a docker login command.  Execute the generated command.
#   > docker push 469205354006.dkr.ecr.us-east-1.amazonaws.com/fsoi-batch

# 2. Create a zip file with code for AWS Lambda and copy it to s3://jcsda-scratch/fsoi_lambda.zip
#   > ./build/update_lambda.sh

# 3a. Launch the CloudFormation stack (if the stack is NOT already running):
#   > aws cloudformation create-stack --stack-name IOSingest --template-body \
#   >     fileb://resources/cloudformation_ios_data_ingest.yaml
#   Progress can be monitored on the AWS Console under the CloudFormation service

# 3b. Update the CloudFormation stack (if the stack IS already running):
#   > aws cloudformation update-stack --stack-name IOSingest --template-body \
#   >     fileb://resources/cloudformation_ios_data_ingest.yaml
#   # Update lambda code if it has changed:
#   > aws lambda update-function-code --function-name fsoi_ingest_nrl --s3-bucket jcsda-scratch \
#         --s3-key fsoi_lambda.zip

# 4. Stack will be deployed.  The CloudWatch Event Rule will call the Lambda function once
#    per day for the NRL ingest.  The ingest function will submit a Batch job if file download
#    was successful.  If files are not available, a monitoring message will be sent to hahnd@ucar.edu.

echo "Read the comments in this script instead of running it."
