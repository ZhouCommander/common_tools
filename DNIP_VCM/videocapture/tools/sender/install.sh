#!/bin/bash
CURRENT_DIR=$(cd `dirname $0`; pwd)
sudo pip install pika
sudo pip install python-etcd

RED='\033[1;31m'
YELLOW='\033[1;33m'
NO_COLOR='\033[0m'

check_failed=0
if [ "$VIDEO_DIR" = "" ]
then
  printf "${RED}error: video dir is needed. Please export VIDEO_DIR before install.${NO_COLOR}\n"
  check_failed=1
fi

if [ "$VIDEO_BAK_DIR" = "" ]
then
  printf "${RED}error: video backup dir is needed. Please export VIDEO_BAK_DIR before install.${NO_COLOR}\n"
  check_failed=1
fi

if [ $check_failed = 1 ]
then
    exit 1
fi
appmgc reg -n scan_videos -c "python ${CURRENT_DIR}/scan_videos.py ${VIDEO_DIR} ${VIDEO_BAK_DIR}" -u root -w "${CURRENT_DIR}" -f -t "`date  +\"%Y-%m-%d %H:%M:%S\"`" -i 600
