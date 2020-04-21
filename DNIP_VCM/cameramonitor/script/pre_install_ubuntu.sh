#!/bin/bash
if [ "$ETCD_URLS" = "" ]
then
  printf "${RED}error:Must export ETCD_URLS before install.${NO_COLOR}\n"
  exit 1
fi

if [ "$CAPTURE_JSON_PATH" = "" ]
then
  printf "${RED}error:Must export CAPTURE_JSON_PATH before install.${NO_COLOR}\n"
  exit 1
fi