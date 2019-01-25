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
#   > aws cloudformation create-stack --stack-name IOSwebapp --template-body \
#   >     fileb://resources/cloudformation_ios_fsoi_web.yaml
#   Progress can be monitored on the AWS Console under the CloudFormation service

# 3b. Update the CloudFormation stack (if the stack IS already running):
#   > aws cloudformation update-stack --stack-name IOSwebapp --template-body \
#   >     fileb://resources/cloudformation_ios_fsoi_web.yaml
#   # Update lambda code if it has changed:
#   > aws lambda

# 4. Until API Gateway v2 is supported in CloudFormation, create it manually from the console:
#   a. Create a new API with WEBSOCKET protocol.
#   b. Find the API in the menu on the left of the screen and click on it, then Route under the menu.
#   c. Click the [+] button on $default route, and choose:
#     i. Integration Type: Lambda Function
#     ii. Use Lambda Proxy Integration: checked
#     iii. Lambda Region: us-east-1
#     iv. Lambda Function: fsoi_request_handler
#     v. Invoke with caller credentials: not checked
#     vi. Execution role: empty
#     vii. Use default connection timeout: not checked
#     viii. Custom Timeout: 29000
#   d. Click the SAVE button bottom right.
#   e. Click the ACTIONS button at the top and select DEPLOY API
#     i. Deployment stage: v1
#     ii. Deployment description: empty or a description
#   f. Click DEPLOY
#   g. Click on STAGES, then v1.  The WSS URL at the top needs to be added to the front-end code,
#      however, if this API already existed, the URL probably did not change and no action is
#      required.

# 5. Deploy the front-end Angular code:
#   > cd webapp
#   > ./deploy.sh
#   This will run 'ng-build --prod' on the front-end code and copy the result to s3://ios.jcsda.org.

# 6. Web application should be ready to go at http://ios.jcsda.org.  If the HTTPS protocol is desired
#    in the future, CloudFront can be used.  Note that updates when using CloudFront are not
#    instantaneous, so it is less desirable to use for development, but is good for production.

echo "Read the comments in this script instead of running it."
