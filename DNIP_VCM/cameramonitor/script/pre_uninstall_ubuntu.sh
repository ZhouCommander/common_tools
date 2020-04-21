#!/bin/bash
appmgc unreg -n cameramonitor -f 
appmgc query | grep camera_ | awk '{cmd="appmgc unreg -f -n "$6;system(cmd)}'