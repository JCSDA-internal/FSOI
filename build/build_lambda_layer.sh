#! /bin/bash

# This script builds a zip file that can be used as an AWS Lambda
# Layer as the third party dependencies for the FSOI web application.

# Check at least that we're running on Amazon Linux 2
if [[ $(uname -s) != 'Linux' ]]; then
    if [[ $(echo $(uname -r) | grep -o amzn2) != 'amzn2' ]]; then
        echo "NOTE: This script needs to run on a server/container with the same architecture as AWS Lambda."
        echo "Native libraries will be downloaded with some of the python packages and running this on the"
        echo "wrong architecture will cause the wrong libraries to be downloaded, resulting in runtime errors"
        echo "on AWS."
        exit 1
    fi
fi

# set the directories to use
root_dir=$(pwd)
build_dir="${root_dir}/ios-libs-layer"

# download the python dependencies
mkdir -p ${build_dir}/python/libs
cd ${build_dir}/python/libs
pip3 install -t . chardet requests urllib3 certifi idna pandas python-dateutil pytz six pyyaml pyparsing cycler kiwisolver numexpr mock tables bokeh selenium phantomjs

# result is too big for a lambda layer (250 MB limit at time of writing
# (2020-Feb-18)), so some of the packages need to be trimmed down to fit.
cd ${build_dir}/python/libs
rm -Rf pandas/tests
find . -type d -name \*-info -exec rm -Rf {} \;

cd ${build_dir}/python/libs/bokeh/server/static/js
rm compiler.js compiler.js.map compiler.json bokeh.json bokeh-es6.js*

# download phantomjs, which is required by Bokeh to make static images
cd ${build_dir}
wget https://bitbucket.org/ariya/phantomjs/downloads/phantomjs-2.1.1-linux-x86_64.tar.bz2
tar -xBf phantomjs-2.1.1-linux-x86_64.tar.bz2
mv phantomjs-2.1.1-linux-x86_64 phantomjs
rm phantomjs-2.1.1-linux-x86_64.tar.bz2 

# result is too big for a lambda layer (250 MB limit at time of writing
# (2020-Feb-18)), so some of the packages need to be trimmed down to fit.
cd ${build_dir}/phantomjs
rm -Rf ChangeLog examples/ LICENSE.BSD README.md third-party.txt

# make sure the permissions are set correctly on all of the files
cd ${build_dir}
find . -exec chmod 755 {} \;
rm -f ${root_dir}/ios-libs-layer.zip
zip -r ${root_dir}/ios-libs-layer.zip python phantomjs

# upload the layer code to S3 bucket
echo "*** Action Required ***"
echo "Run the following command to upload the zip file to S3"
echo aws s3 cp ${root_dir}/ios-libs-layer.zip s3://fsoi/CodeBuild/ios-libs-layer-$(date +%s).zip
