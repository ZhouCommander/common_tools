VERSION = 2.4
BUILLD_DATE =`date  +%Y%m%d%H%M%S`

INTSALL_NAME = scan-videos
INTSALL_DIR = scan_videos

all:
	make package
	make deb
package:
	pyinstaller -F scan_videos.py -n ${INTSALL_DIR}
rpm:
	fpm -s dir -t rpm -v ${VERSION} -n ${INTSALL_NAME} --vendor "deepnorth" --description "deepnorth" -C ./release
	rm -rf "${TEMP_DIR}"
deb:
	cp dist/scan_videos .
	tar -zcf scan_videos.tar.gz scan_videos scan_videos.json
clean:
	-rm -f scan_videos.tar.gz
	-rm -f scan_videos
	-rm ${INTSALL_DIR}.spec
	-rm -rf build
	-rm -rf dist