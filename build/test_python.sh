#! /bin/sh

# set the correct readlink executable
readlink=readlink
if [[ $(uname -s) == "Darwin" ]]; then
  readlink=greadlink
fi

# find the root directory of the git repository
root_dir=$(${readlink} -f $(dirname $0)/..)

# run the tests and code coverage tool
cd ${root_dir}/python/test
export PYTHONPATH="${root_dir}/python/src:${root_dir}/python/test"
coverage run $(which py.test) .
status=$?
coverage html --include=src/fsoi/\*\*/\*.py
exit $status
