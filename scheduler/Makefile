VERSION = 2.4
INSTALL_PATH = /opt/deepnorth/scheduler
TEMP_DIR = release/${INSTALL_PATH}
ARCH = x86_64
NFS_BASE = /nfs/BaseGroup
BUILLD_DATE =`date  +%Y%m%d%H%M%S`
all:
	make package
	make package_x86
	make deb
arm64:
	make package
	make package_arm64
	make deb
package:
	sed -i "s#__BUILD_DATE__#${BUILLD_DATE}#g" ./src/main.py
	sed -i "s#__BUILD_VERSION__#${VERSION}#g" ./src/main.py
	pyinstaller -F ./src/main.py -n scheduler --hidden-import shapely --hidden-import retrying --runtime-tmpdir /deepruntime \
	--hidden-import cv2 --hidden-import torch --hidden-import torchvision  --hidden-import sklearn --hidden-import numba --hidden-import sklearn.decomposition --hidden-import sklearn.neighbors.typedefs \
	--hidden-import colorsys --add-binary /nfs/BaseGroup/internal/algo_framework/python_lib/x86_64/libgeos_c.so:./ \

	cp -rf ../algo_framework ./dist
	cp -rf ../db_connection/aes.py ./dist/algo_framework/src/common/
	mkdir ./dist/release
	mv ./dist/scheduler ./dist/release/
	mv ./dist/release ./dist/scheduler

	cp -rf conf ./dist/scheduler/
	cp ../../python/common/rabbitmq_wrapper/rabbitmq_wrapper.json ./dist/scheduler/conf

	dos2unix script/*.sh
	cp -rf script ./dist/scheduler/
	#cp -rf "${NFS_BASE}/internal/algo_framework/data" ./dist/algo_framework/src
	cp -rf "${NFS_BASE}/internal/algo_framework/model" ./dist/algo_framework/src
package_x86:
	#cp -f "${NFS_BASE}/3rdparty/sunergy/x86_64/libmoonergy.so.8" ./dist/algo_framework/libs
	#cp -f "${NFS_BASE}/3rdparty/sunergy/x86_64/libsunergy.so.8" ./dist/algo_framework/libs
	cp -f "${NFS_BASE}/3rdparty/sunergy/x86_64/libmoonergy.so.10" ./dist/algo_framework/libs
	cp -f "${NFS_BASE}/3rdparty/sunergy/x86_64/libsunergy.so.10" ./dist/algo_framework/libs
	cp -f "${NFS_BASE}/3rdparty/sunergy/x86_64/libtrack.so" ./dist/algo_framework/libs
	cp -f "${NFS_BASE}/3rdparty/sunergy/x86_64/_bbox_associate.so" ./dist/algo_framework/libs
	cp -f "${NFS_BASE}/3rdparty/sunergy/x86_64/libDeepNorthDetection_OpenVINO.so" ./dist/algo_framework/libs/libDeepNorthDetection_OpenVINO.so

	#cp -prf ${NFS_BASE}/3rdparty/sunergy/x86_64/libcu* ./dist/algo_framework/libs/
	if [ ! -d "${TEMP_DIR}" ]; then \
		mkdir -p ${TEMP_DIR}; \
	fi
	mv ./dist/*   ${TEMP_DIR}

	# build cmd
	# mkdir -p ${TEMP_DIR}/scheduler/bin
	# sed -i "s#__BUILD_DATE__#${BUILLD_DATE}#g" ./src/cmd/dhosts.py
	# sed -i "s#__BUILD_VERSION__#${VERSION}#g" ./src/cmd/dhosts.py
	# pyinstaller -F -p ./src/ -p ../../python/ ./src/cmd/dhosts.py
	# mv ./dist/dhosts ${TEMP_DIR}/scheduler/bin

	# sed -i "s#__BUILD_DATE__#${BUILLD_DATE}#g" ./src/cmd/dqueues.py
	# sed -i "s#__BUILD_VERSION__#${VERSION}#g" ./src/cmd/dqueues.py
	# pyinstaller -F -p ./src/ -p ../../python/ ./src/cmd/dqueues.py
	# mv ./dist/dqueues ${TEMP_DIR}/scheduler/bin

package_arm64:
	cp -rf ${NFS_BASE}/3rdparty/sunergy/arm_64/libsunergy* ./dist/algo_framework/libs
	cp -rf "${NFS_BASE}/3rdparty/sunergy/arm_64/libtrack.so" ./dist/algo_framework/libs
	#cp -prf ${NFS_BASE}/3rdparty/sunergy/x86_64/libcu* ./dist/algo_framework/libs/
	if [ ! -d "${TEMP_DIR}" ]; then \
		mkdir -p ${TEMP_DIR}; \
	fi
	mv ./dist/*   ${TEMP_DIR}
rpm:
	fpm -s dir -t rpm -v ${VERSION} -n scheduler --vendor "deepnorth" --description "deepnorth" -C ./release
	rm -rf "${TEMP_DIR}"
deb:
	fpm -s dir -t deb -v ${VERSION} -n scheduler --vendor "deepnorth" --description "deepnorth" --pre-install ${TEMP_DIR}/scheduler/script/pre_install_ubuntu.sh --post-install ${TEMP_DIR}/scheduler/script/install_ubuntu.sh --before-remove ${TEMP_DIR}/scheduler/script/pre_uninstall_ubuntu.sh -C ./release
	rm -rf ./release
clean:
	sed -i "s/^.*BUILD_DATE = .*/BUILD_DATE = '__BUILD_DATE__'/" ./src/main.py
	sed -i "s/^.*BUILD_VERSION = .*/BUILD_VERSION = '__BUILD_VERSION__'/" ./src/main.py

	# sed -i "s/^.*BUILD_DATE = .*/BUILD_DATE = '__BUILD_DATE__'/" ./src/cmd/dhosts.py
	# sed -i "s/^.*BUILD_VERSION = .*/BUILD_VERSION = '__BUILD_VERSION__'/" ./src/cmd/dhosts.py

	# sed -i "s/^.*BUILD_DATE = .*/BUILD_DATE = '__BUILD_DATE__'/" ./src/cmd/dqueues.py
	# sed -i "s/^.*BUILD_VERSION = .*/BUILD_VERSION = '__BUILD_VERSION__'/" ./src/cmd/dqueues.py
	rm -rf dist
	rm -rf build
	rm -rf ./release
	rm -rf scheduler.spec
	# rm -rf dhosts.spec
	# rm -rf dqueues.spec
	rm -f .spec
	rm *.deb

