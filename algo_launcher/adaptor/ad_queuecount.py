import json
import argparse
import os, sys
import subprocess
import time
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


algo_folder_name = 'pose'
rest_sql_folder = "rest_sql"
os.chdir('{}/Algo_Bucket/{}'.format(NFS_folder,algo_folder_name))
sys.path.append('{}/Algo_Bucket/{}'.format(NFS_folder,algo_folder_name))
rest_sql_folder_path = "{}/{}".format(NFS_folder,rest_sql_folder)
algo_sql_folder_path = "{}/{}/{}".format(NFS_folder,rest_sql_folder,algo_folder_name)
config = json.loads(body)
if sql_model != "sql":
    if not os.path.exists(rest_sql_folder_path) :
        try:
            os.mkdir(rest_sql_folder_path,0777)
            os.chmod(rest_sql_folder_path,0777)
        except Exception as e:
            print e
    if not os.path.exists(algo_sql_folder_path) :
        try:
            os.mkdir(algo_sql_folder_path,0777)
            os.chmod(algo_sql_folder_path,0777)
        except Exception as e:
            print e
####################  algo  ##############################################



import time
import os
import connect_db
import lib.pose_tools.pose as pose

def polygon_zones_to_algo_zones(polygon_zones):
    service_zones = []
    tmp = []
    for index, value in enumerate(polygon_zones):
        print index, value
        for v in value:
            tmp.append(float(v.get('x')))
            tmp.append(float(v.get('y')))
        print tmp
        service_zones.append(tmp)
        tmp = []
    print "service_zones is {0}".format(service_zones)
    return service_zones


def algorithm_return(frame_paths, queue_zones, gpu_idx):
    PoseEvent = pose.PoseApp("./model/coco.data", "./model/openpose.cfg",
                             "./model/openpose.weight", gpu_idx=gpu_idx)
    each_zone_person_number = PoseEvent.count_queue_person(frame_paths, queue_zones)

    PoseEvent.free()

    print "each_zone_person_number is {0}".format(each_zone_person_number)
    return each_zone_person_number


def write_db(polygon_ids, img_paths, polygon_zones, gpu_idx):

    # queue_zones = [[0.72, 0.283, 0.381, 0.476, 0.564, 0.994, 0.997, 0.994, 0.997, 0.449],
    # [0.374, 0.081, 0.374, 0.324, 0.604, 0.324, 0.604, 0.081]]
    # each_zone_person_number = [[1, 2, 3, 4], [5, 6, 7, 8], [2, 1, 3, 2]]

    queue_zones = polygon_zones_to_algo_zones(polygon_zones)
    each_zone_person_number = algorithm_return(img_paths, queue_zones, gpu_idx)

    polygon_zone_dict = {}
    for p_id, each_zone_person in zip(polygon_ids, each_zone_person_number):
        print p_id, each_zone_person
        polygon_zone_dict[p_id] = each_zone_person

    print polygon_zone_dict

    conn = connect_db.db_init()
    cursor = conn.cursor()
    date_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    dic_data = {
        "operations":
        {
            "insert":
            {
                "table": "queuecount",
                "columns": ["polygon_id", "timestamp", "counting","update_time"],
                "values": []
            }
        },
        "date_time": date_time,
        "from_process": "ad_queuecount"
    }

    for polygon_id, polygon_zone_list in polygon_zone_dict.iteritems():
        for index, frame_path in enumerate(img_paths):
            jpg_date_time = frame_path.split('/')[-1][-23:-4].replace('_', ' ')
            print polygon_id, jpg_date_time, polygon_zone_list[index]
            if sql_model == "sql":
                insert_sql = '''INSERT INTO queuecount (polygon_id, timestamp, counting, update_time)
                    VALUES ('{polygon_id}', '{timestamp}', '{counting}', '{update_time}')'''.format(
                        polygon_id=polygon_id, timestamp=jpg_date_time, counting=polygon_zone_list[index],
                        update_time=time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))

                print "insert_sql is {0}".format(insert_sql)
                cursor.execute(insert_sql)
                conn.commit()
            else:    
                time_now = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
                dic_data["operations"]["insert"]["values"].append([polygon_id, jpg_date_time, polygon_zone_list[index],time_now])
    if sql_model == "sql":
        cursor.close()
        conn.close()
    else:
        json_data = json.dumps(dic_data)
        sql_data_file_path = sql_data_file_path = "{}/sql_data_{}.json".format(algo_sql_folder_path,date_time)
        try:
            with open(sql_data_file_path,'w') as f:
                f.write(json_data)
        except Exception as e:
            print e

video_paths = config.get("videoname")
polygon_zones = config.get("polygonSpec")
polygon_ids = config.get("polygonId")
gpu = int(GPU_idx)

write_db(polygon_ids, video_paths, polygon_zones, gpu)