# VideoCapture 
# Features

  - Capture video from RTSP stream
  - Send capture result to Message Queue
  - Return exit code in different error case


# Build

```sh
$ sudo -s
$ git clone https://github.com/VMaxxInc/common-component.git
$ cd common-component/cpp/videocapture/
$ make
$ make deb
```
  - install package is **videocapture_2.4_amd64.deb**

# Install
```sh
$ sudo -s
$ sudo apt-get install ./videocapture_2.4_amd64.deb
```
# Uninstall
```sh
$ sudo -s
$ apt-get remove videocapture
```





### tools: sender
For testing, manually push the video file into the corresponding queue for MQ.

Installing dependent components:
```sh
sudo pip install pika
```

help:
```sh
python sender.py
```

example:
```sh
python sender.py QUEUE_NAME MSG_JSON_STR
python sender.py cam_1 '{"capture_duration_seconds": 300, "camera_id": 3, "capture_time": "2018-12-15 17:40:12", "file_path": "/mnt/xxx/3_2018-12-15-17-40-12_300.mp4"}'
```
The json string needs to be filled out according to the actual video file.