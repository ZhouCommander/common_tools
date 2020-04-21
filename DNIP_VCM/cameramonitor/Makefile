VERSION=2.4
PACKAGE_NAME=camera-capture
BUILD_DATE=$(shell date "+%Y%m%d%H%M")
BUILD_TAG=${PACKAGE_NAME}-${VERSION}-${BUILD_DATE}

RELEASE_DIR = ./release
INSTALL_PATH = opt/deepnorth/cameracapture
TEMP_DIR = ${RELEASE_DIR}/${INSTALL_PATH}

all:
	echo ${BUILD_TAG}
	cd ../videocapture;make
	cd cameramonitor; make
	make build_dir
	make deb

build_dir:
	if [ ! -d "${TEMP_DIR}" ]; then \
		mkdir -p ${TEMP_DIR}; \
	fi
	cp ./cameramonitor/cameramonitor ${TEMP_DIR}
	cp ./cameramonitor/cameramonitor.json ${TEMP_DIR}
	cp -rf ./script/*.sh  ${TEMP_DIR}
	chmod +x ${TEMP_DIR}/*.sh
	dos2unix  ${TEMP_DIR}/*.sh
rpm:
	fpm -s dir -t rpm -v ${VERSION} -n ${PACKAGE_NAME} --vendor "deepnorth" --description "deepnorth" --pre-install ${TEMP_DIR}/pre_install_ubuntu.sh --post-install ${TEMP_DIR}/install_ubuntu.sh --before-remove ${TEMP_DIR}/pre_uninstall_ubuntu.sh --after-remove ${TEMP_DIR}/uninstall_ubuntu.sh -C ${RELEASE_DIR}
	rm -rf ${TEMP_DIR}
deb:
	fpm -s dir -t deb -v ${VERSION} -n ${PACKAGE_NAME} --vendor "deepnorth" --description "deepnorth" --pre-install ${TEMP_DIR}/pre_install_ubuntu.sh --post-install ${TEMP_DIR}/install_ubuntu.sh --before-remove ${TEMP_DIR}/pre_uninstall_ubuntu.sh --after-remove ${TEMP_DIR}/uninstall_ubuntu.sh -C ${RELEASE_DIR}
	rm -rf ${TEMP_DIR}

clean:
	cd cameramonitor; make clean
	rm -rf release
	rm -f *.rpm *.deb
