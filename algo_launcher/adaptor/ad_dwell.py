import json
import argparse
import os, sys
import subprocess

#########################  Adaptor Template Part #######################

# add Argument
parser = argparse.ArgumentParser()
parser.add_argument("--message", help="Queue message")
parser.add_argument("--gpu_index", help="Target gpu")
parser.add_argument("--nfs", help="Local nfs path")
parser.add_argument("--sql_model", help="execute sql model")
args = parser.parse_args()

body = args.message
GPU_idx = args.gpu_index
NFS_folder = args.nfs
sql_model = args.sql_model
########################################################################

''' Custom Part '''


algo_folder_name = 'dwell'

os.chdir('{}/Algo_Bucket/{}'.format(NFS_folder,algo_folder_name))
sys.path.append('{}/Algo_Bucket/{}'.format(NFS_folder,algo_folder_name))
config = json.loads(body)

####################  algo  ##############################################


# os.chdir('/home/fang/program/Local_Farm/Algo_Bucket/dwell')
# sys.path.append('/home/fang/program/Local_Farm/Algo_Bucket/dwell')

from get_reId_and_imageTime import HandleVideos


def run_dwell(gpu_id, video_list):
    if video_list != []:
        capture = HandleVideos(gpu_id)
        capture.handle_videos(video_list)
    else:
        print video_list, "dose not exists."

vname = config.get('videoname')
gpu = int(GPU_idx)

run_dwell(gpu, vname)

