# scheduler

# Features

  - Collecting host GPU, MEM and CPU information
  - Scheduling tasks to different host
  - Automatically discover available host resources
  - Statistical scheduling result

# Build
```sh
$ sudo -s
$ git clone https://github.com/DeepNorthAI/common-component.git
$ cd common-component/python/scheduler/
$ make
```
  - install package is **scheduler_2.4_amd64.deb**

# Install

Name | Desc
---|---
Scope | Install on all GPU Host
RunHost | GPU Host
Dependency | App-Manager, ETCD.

Environment Parameter | Desc | Example
---|---|---
ETCD_URLS| ETCD url(http://192.168.1.100:2379). (For etcd cluster pls use http://192.168.1.151:2379,http://192.168.1.158:2379) | http://192.168.1.151:2379
GPU_TOTAL_NUMBER| Specify the number of gpus to use | 1

```sh
$ sudo -s
$ export ETCD_URLS=http://192.168.1.100:2379
$ apt-get install ./scheduler_2.4_amd64.deb
```

# Verify
```sh
$ query | grep scheduler
  2  root  start  17755 255    scheduler   /opt/deepnorth/scheduler/scheduler/scheduler
```

# UnInstall
```sh
$ dpkg -P scheduler
```


# Specify the number of GPUs
Specify the number of GPUs to use, you need to export GPU_TOTAL_NUMBER 
environment variables at installation. GPU_TOTAL_NUMBER=5 means will use GPU: 0/1/2/3/4

For example:

$ export ETCD_URLS=http://192.168.1.100:2379
$ export GPU_TOTAL_NUMBER=4
$ apt-get install ./scheduler_2.4_amd64.deb

When scheduler is launched, it can only use 4 GPUs.

If scheduler is already installed, execute the following command to re-register scheduler:

$ appmgc reg -n scheduler -c "/opt/deepnorth/scheduler/scheduler/scheduler --gpus 4" -u root -w /opt/deepnorth/scheduler/scheduler  -f -e "LD_LIBRARY_PATH=/opt/deepnorth/scheduler/algo_framework/libs"
