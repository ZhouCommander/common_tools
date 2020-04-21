#!/bin/bash
INSTALL_PATH=/opt/deepnorth/cameracapture
sed -i "s#@etcd_urls@#${ETCD_URLS}#g" ${INSTALL_PATH}/cameramonitor.json 
sed -i "s#@rest_scan_path@#${CAPTURE_JSON_PATH}#g" ${INSTALL_PATH}/cameramonitor.json
appmgc reg -n cameramonitor -c "${INSTALL_PATH}/cameramonitor ${CAPTURE_JSON_PATH}" -u root -w ${INSTALL_PATH}  -f -e "LOG_LEVEL=WARN"
