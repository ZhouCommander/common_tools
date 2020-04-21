#!/bin/bash
check_failed=0
if [ "$REST_URL" = "" ]
then
  echo "error: Rest url needed. Please export REST_URL before install."
  check_failed=1
fi

if [ "$REST_CLIENT_ID" = "" ]
then
  echo "error: Client ID needed. Please export REST_CLIENT_ID before install."
  check_failed=1
fi

if [ "$REST_CLIENT_SECRET" = "" ]
then
  echo "error: Client secret needed. Please export REST_CLIENT_SECRET before install."
  check_failed=1
fi

if [ "$REST_USER_NAME" = "" ]
then
  echo "error: User name needed. Please export REST_USER_NAME before install."
  check_failed=1
fi

if [ "$REST_PASSWORD" = "" ]
then
  echo "error: Password needed. Please export REST_PASSWORD before install."
  check_failed=1
fi

if [ "$UPLOAD_CLOUD_PATH" = "" ]
then
  echo "error: Cloud path needed. Please export UPLOAD_CLOUD_PATH before install."
  check_failed=1
fi


if [ $check_failed = 1 ]
then
    exit 1
fi

if [ "$LOCAL_PIC_SAVE_DIR" = "" ]
then
  echo "warnning: Use default local pic save dir ''. Please export LOCAL_PIC_SAVE_DIR before install if you want to configure it."
fi

if [ "$URL_PREFIX" = "" ]
then
  echo "warnning: Use default url prefix ''. Please export URL_PREFIX before install if you want to configure it."
fi

if [ "$SCAN_SLEEP_INTERVAL" = "" ]
then
  echo "warnning: Use default sleep interval '2'. Please export SCAN_SLEEP_INTERVAL before install if you want to configure it."
fi

if [ "$SCAN_LOOP_NUM" = "" ]
then
  echo "warnning: Use default loop num '1800'. Please export SCAN_LOOP_NUM before install if you want to configure it."
fi

if [ "$REST_OAUTH_PATH" = "" ]
then
  echo "warnning: Use default oauth path '/oauth/token'. Please export REST_OAUTH_PATH before install if you want to configure it."
fi

if [ "$REST_GRANT_TYPE" = "" ]
then
  echo "warnning: Use default grant type 'password'. Please export REST_GRANT_TYPE before install if you want to configure it."
fi

if [ "$REST_SCOPE" = "" ]
then
  echo "warnning: Use default scope ''. Please export REST_SCOPE before install if you want to configure it."
fi

if [ "$REST_DEBUG_SQL" = "" ]
then
  echo "warnning: Use default debug sql 'false'. Please export REST_DEBUG_SQL before install if you want to configure it."
fi

if [ "$REST_RETRY_NUM" = "" ]
then
  echo "warnning: Use default retry num '3'. Please export REST_RETRY_NUM before install if you want to configure it."
fi

if [ "$UPLOAD_TIMEOUT" = "" ]
then
  echo "warnning: Use default timeout '10'. Please export UPLOAD_TIMEOUT before install if you want to configure it."
fi

if [ "$UPLOAD_THREAD_NUM" = "" ]
then
  echo "warnning: Use default thread num '5'. Please export UPLOAD_THREAD_NUM before install if you want to configure it."
fi


exit 0