#! /bin/sh

# set the correct readlink executable
readlink=readlink
if [[ $(uname -s) == "Darwin" ]]; then
  readlink=greadlink
fi

# find the root directory of the git repository
root_dir=$(${readlink} -f $(dirname $0)/..)

# run the pylint checks
pylint --rcfile=${root_dir}/build/.pylintrc -E ${root_dir}/python/src/fsoi

# check the pylint exit code
status=$?
if [[ ${status} != 0 ]]; then
  echo "Pylint checks failed"
fi

# print success message
echo "Passed."
exit $status
