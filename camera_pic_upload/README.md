# camera_pic_upload
# Features

  - Scan table vm_camera_picture_collect in database.
  - Process all records, capture a picture, send to azure or save to local dir, update table vm_camera_picture_collect and vm_camera.
  - Only one camera_pic_upload can be installed in the same environment.

# Build
```sh
$ sudo -s
$ cd common-tools/python/camera_pic_upload/
$ make
```
  - install package is **camera-pic-upload_2.4_amd64.deb**
