#!/bin/bash

TOP_PATH=/opt/deepnorth/scheduler
sed -i "s#@ETCD_URLS@#${ETCD_URLS}#g" ${TOP_PATH}/scheduler/conf/scheduler.json

RMQ_CONF="${TOP_PATH}/scheduler/conf/rabbitmq_wrapper.json"
if [ "$RMQ_HOST" = "" ] && [ "$RMQ_PORT" = "" ]
then
    rm -rf ${RMQ_CONF}
else
    if [ "$RMQ_HOST" = "" ]
    then
      RMQ_HOST="localhost"
    fi

    if [ "$RMQ_PORT" = "" ]
    then
      RMQ_PORT=5672
    fi

    sed -i "s#@RMQ_HOST@#${RMQ_HOST}#g" ${RMQ_CONF}
    sed -i "s#@RMQ_PORT@#${RMQ_PORT}#g" ${RMQ_CONF}
fi

if [ -z ${GPU_TOTAL_NUMBER} ]
then
  CMD="${TOP_PATH}/scheduler/scheduler"
else
  CMD="${TOP_PATH}/scheduler/scheduler --gpus ${GPU_TOTAL_NUMBER}"
fi

ALGO_PATH=${TOP_PATH}/algo_framework/libs

rm -rf ${ALGO_PATH}/libsunergy.so
rm -rf ${ALGO_PATH}/libmoonergy.so

ln -s ${ALGO_PATH}/libsunergy.so.10 ${ALGO_PATH}/libsunergy.so
ln -s ${ALGO_PATH}/libmoonergy.so.10 ${ALGO_PATH}/libmoonergy.so

mkdir -p "/deepruntime"
appmgc reg -n scheduler -c "${CMD}" -u root -w ${TOP_PATH}/scheduler  -f -e "LD_LIBRARY_PATH=${TOP_PATH}/algo_framework/libs" \
-t "2019-01-01 04:30:00" -i 86400 -k true
