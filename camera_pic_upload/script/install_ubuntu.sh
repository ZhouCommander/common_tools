#!/bin/bash
INSTALL_NAME=camera_pic_upload
INSTALL_PATH=/opt/deepnorth/${INSTALL_NAME}
if [ "$REST_OAUTH_PATH" = "" ]
then
  REST_OAUTH_PATH="/oauth/token"
fi

if [ "$REST_GRANT_TYPE" = "" ]
then
    REST_GRANT_TYPE="password"
fi

if [ "$REST_SCOPE" = "" ]
then
  REST_SCOPE=""
fi

if [ "$REST_DEBUG_SQL" = "" ]
then
  REST_DEBUG_SQL="false"
else
  REST_DEBUG_SQL="true"
fi

if [ "$REST_RETRY_NUM" = "" ]
then
  REST_RETRY_NUM=3
fi

if [ "$SCAN_SLEEP_INTERVAL" = "" ]
then
  SCAN_SLEEP_INTERVAL=2
fi

if [ "$SCAN_LOOP_NUM" = "" ]
then
  SCAN_LOOP_NUM=1800
fi

if [ "$LOCAL_PIC_SAVE_DIR" = "" ]
then
  LOCAL_PIC_SAVE_DIR=""
fi

if [ "$URL_PREFIX" = "" ]
then
  URL_PREFIX=""
fi

if [ "$UPLOAD_TIMEOUT" = "" ]
then
  UPLOAD_TIMEOUT=10
fi

if [ "$UPLOAD_THREAD_NUM" = "" ]
then
  UPLOAD_THREAD_NUM=5
fi

if [ "$IMG_PATH" = "" ]
then
  IMG_PATH=""
fi

sed -i "s#@REST_URL@#${REST_URL}#g" ${INSTALL_PATH}/rest_sql_wrapper.json
sed -i "s#@REST_OAUTH_PATH@#${REST_OAUTH_PATH}#g" ${INSTALL_PATH}/rest_sql_wrapper.json
sed -i "s#@REST_GRANT_TYPE@#${REST_GRANT_TYPE}#g" ${INSTALL_PATH}/rest_sql_wrapper.json
sed -i "s#@REST_CLIENT_ID@#${REST_CLIENT_ID}#g" ${INSTALL_PATH}/rest_sql_wrapper.json
sed -i "s#@REST_CLIENT_SECRET@#${REST_CLIENT_SECRET}#g" ${INSTALL_PATH}/rest_sql_wrapper.json
sed -i "s#@REST_USER_NAME@#${REST_USER_NAME}#g" ${INSTALL_PATH}/rest_sql_wrapper.json
sed -i "s#@REST_PASSWORD@#${REST_PASSWORD}#g" ${INSTALL_PATH}/rest_sql_wrapper.json
sed -i "s#@REST_SCOPE@#${REST_SCOPE}#g" ${INSTALL_PATH}/rest_sql_wrapper.json
sed -i "s#@REST_DEBUG_SQL@#${REST_DEBUG_SQL}#g" ${INSTALL_PATH}/rest_sql_wrapper.json
sed -i "s#@REST_RETRY_NUM@#${REST_RETRY_NUM}#g" ${INSTALL_PATH}/rest_sql_wrapper.json
mkdir -p "/opt/deepnorth/work"
appmgc reg -n camera-pic-upload -c "${INSTALL_PATH}/camera_pic_upload --timeout ${UPLOAD_TIMEOUT} --cloudpath \"${UPLOAD_CLOUD_PATH}\" --interval ${SCAN_SLEEP_INTERVAL} --loopnum ${SCAN_LOOP_NUM} --local \"${LOCAL_PIC_SAVE_DIR}\" --urlpref \"${URL_PREFIX}\" --imgpath \"${IMG_PATH}\"" -u root -w "${INSTALL_PATH}" -f -t "`date  +\"%Y-%m-%d %H:%M:%S\"`" -i 3600 -k true