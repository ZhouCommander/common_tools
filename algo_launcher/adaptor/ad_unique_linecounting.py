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


algo_folder_name = 'unique_people'

os.chdir('{}/Algo_Bucket/{}'.format(NFS_folder,algo_folder_name))
sys.path.append('{}/Algo_Bucket/{}'.format(NFS_folder,algo_folder_name))
config = json.loads(body)

####################  algo  ##############################################

cm = "python deep_sort_server.py"

if config.has_key('videoname'):
    input_dir = " -input_dir " + config.get('videoname')[0]
    cm = cm + input_dir

if config.has_key('lineId'):
    lineID_list = config.get('lineId')
    if lineID_list:
        lineIDs = ' '.join(lineID_list)
        cm = cm + " -polylineIDs "+lineIDs
        for line in config.get('lineSpec'):
            p_list = []
            for point in line:
                p_list.append(point.get('x'))
                p_list.append(point.get('y'))
            lineSpec = ' '.join(p_list)
            cm = cm + ' -polyline '+ lineSpec

if config.has_key('polygonId'):
    polyID_list = config.get('polygonId')
    if polyID_list:
        polyIDs = ' '.join(polyID_list)
        cm = cm + " -polygonIDs "+polyIDs
        for poly in config.get('polygonSpec'):
            p_list = []
            for point in poly:
                p_list.append(point.get('x'))
                p_list.append(point.get('y'))
            lineSpec = ' '.join(p_list)
            cm = cm + ' -polygon '+ lineSpec

if config.has_key('description'):
    cm = cm + " -cam_name " + config.get('description')
    cm = cm + " -cam_id " + config.get('cameraId')

cm = cm + ' -resolution {} -interval {} -type {} -gpu_idx {}'.format(config.get('resolution'),
                                                                         config.get('interval'),
                                                                         config.get('algorithm_type'),
                                                                         GPU_idx)
sys.stdout.write(cm)
sys.stdout.flush()
subprocess.check_call(cm,shell=True)
