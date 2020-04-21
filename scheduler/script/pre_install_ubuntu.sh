#!/bin/bash

RED='\033[1;31m'
NO_COLOR='\033[0m'

REQUIRED_CONFIGS=(
    ETCD_URLS
)

CHECK_CONF_FAILED=0
for config in "${REQUIRED_CONFIGS[@]}"
do
    has_conf=${!config}
    if [ "$has_conf" = "" ]
    then
        printf "${RED}error: config <${config}> is required, please export <${config}> before install${NO_COLOR}\n"
        CHECK_CONF_FAILED=1
    fi
done

if [ $CHECK_CONF_FAILED = 1 ]
then
    exit 1
fi

exit 0
