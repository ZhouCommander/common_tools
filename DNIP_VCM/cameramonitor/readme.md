# CameraMonitor 
# Features

  - Get camera list from ETCD and registe video capture application to capture
  - Write service status to ETCD with TTL when this app started
  - Update Capture status to ETCD (with ttl)
  - Unreg application when un-assigned
  - Update current capture status to ETCD (with ttl)
  - Update capture app when parameter changed


# Build

```sh
$ sudo -s
$ git clone https://github.com/VMaxxInc/common-component.git
$ cd common-component/cpp/cameramonitor/
$ make
```
  - install package is **cameramonitor_2.4_amd64.deb**

# Install
- Please install **App-Manager** **vediocapture** before installing this package.
- export ETCD_HOST and ETCD_PORT,or use default ETCD_HOST=127.0.0.1   ETCD_PORT=2379
- export CAPTURE_JSON_PATH, the path is used by VideoCapture to save json file
```sh
$ sudo -s
$ export ETCD_HOST=192.168.1.151
$ export ETCD_PORT=2379
$ export CAPTURE_JSON_PATH="/data/deepnorth/status"
$ apt-get install ./cameramonitor_2.4_amd64.deb
```
# Uninstall
```sh
$ sudo apt-get remove cameramonitor
```