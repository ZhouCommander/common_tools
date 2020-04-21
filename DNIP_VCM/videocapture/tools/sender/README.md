# Usage

Runtime Python lib Dependency:
```sh
sudo pip install pika
sudo pip install python-etcd
```

# Sender
help:
```sh
python sender.py
```

example:
```sh
python sender.py ${QUEUE_NAME} '{"capture_duration_seconds": 300, "camera_id": 3, "capture_time": "2018-12-15 17:40:12", "file_path": "/mnt/xxx/3_2018-12-15-17-40-12_300.mp4"}'
```

# Scan_videos
Scan_videos will sends all video's in the specified directory to the corresponding RabbitMQ.

Environment Parameter | Desc | Example
---|---|---
VIDEO_DIR| Video directory to be processed |/videos
VIDEO_BAK_DIR | Video archive directory  |/videos_bak

```sh
$ export VIDEO_DIR="/videos"
$ export VIDEO_BAK_DIR="/videos_bak"
$ ./install.sh
```
The installation script "install.sh" registers "scan_videos.py" with Applicatoin Manager as a timed task, runs every 10 minutes, copies video from VIDEO_DIR to VIDEO_BAK_DIR, and sends messages to the MQ queue.

Workflow:
1. Scan and get one video file from $VIDEO_DIR, if the file modify date is 60s ago, then go to step 2.
2. Move this file to $VIDEO_BAK_DIR
3. Send this video file to RabbitMQ with the location from $VIDEO_BAK_DIR

The format of video file name: "camera_id"_YYYY-MM-DD-hh-mm-ss_duration.mp4
example: 23_2019-01-22-00-45-01_300.mp4

The video directory structure is similar to the following:
```sh
$ tree videos
videos/
├── 10
│   ├── 2019-01-25
│   │   ├── 10_2019-01-25-16-10-09_300.mp4
│   │   ├── 10_2019-01-25-16-15-01_300.mp4
│   │   ├── 10_2019-01-25-17-15-00_300.mp4
│   │   └── 10_2019-01-25-17-20-01_300.mp4
│   └── 2019-01-26
├── 11
│   ├── 2019-01-25
│   │   ├── 11_2019-01-25-16-10-09_300.mp4
│   │   ├── 11_2019-01-25-16-15-02_300.mp4
│   │   ├── 11_2019-01-25-17-15-01_300.mp4
│   │   └── 11_2019-01-25-17-20-01_300.mp4
│   └── 2019-01-26
```
help:
```sh
python scan_videos.py
```

example:
```sh
python scan_videos.py VIDEO_DIR  VIDEO_BAK_DIR
python scan_videos.py /videos  /video_bak
```
