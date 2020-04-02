#! /bin/bash

function check_processes()
{
    remaining=$(ps auxwww | grep merra_core | grep ".sh" | grep -v grep | wc | awk \{print\$1\})
    if [[ ${remaining} == "0" ]]; then
      echo "Finished at $(date +%Y-%m-%d_%H:%M:%S)"
      sudo shutdown -h now
    else
      echo "${remaining} processes still running $(date +%Y-%m-%d_%H:%M:%S)"
    fi
}


while [[ 1 == 1 ]]; do

  check_processes
  sleep 10

done
