# camera_pic_upload
# Features

  - Scan table vm_camera_picture_collect in database.
  - Process all records, capture a picture, send to azure or save to local dir, update table vm_camera_picture_collect and vm_camera.
  - Only one camera_pic_upload can be installed in the same environment.

# Build
```sh
$ sudo -s
$ git clone https://github.com/DeepNorthAI/common-component.git
$ cd common-component/python/camera_pic_upload/
$ make
```
  - install package is **camera-pic-upload_2.4_amd64.deb**

# Install
```sh
$ sudo -s
$ export REST_URL="http://192.168.1.151:8084"
$ export REST_CLIENT_ID="2"
$ export REST_CLIENT_SECRET="SZeXsvCiRrAwVnKRvCUnWWHtySApPbn7CK6HfknA"
$ export REST_USER_NAME="support@deepnorth.cn"
$ export REST_PASSWORD="123456"
$ export UPLOAD_TIMEOUT=10
$ export UPLOAD_CLOUD_PATH="dashboardv1_01/adminconsole/"
$ apt-get install ./camera-pic-upload_2.4_amd64.deb
```
If install environment is all in one, add the following two parameters before install:
```sh
$ export LOCAL_PIC_SAVE_DIR="/www/public/capture"
$ export URL_PREFIX="http://ip:port/capture"
```
"/www/public/capture" is one dir under the web service.

if upload local image to Azure, donot use capture, please export $IMG_PATH="/videos", default donot export this param, use capture.

```sh
$ export IMG_PATH="/videos"
```



# Uninstall
```sh
$ sudo apt-get remove camera-pic-upload
```