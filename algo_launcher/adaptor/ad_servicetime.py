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


def checkout(video_paths, polygon_zones, gpu_idx):
    PoseEvent = pose.PoseApp("./model/coco.data", "./model/openpose.cfg",
                             "./model/openpose.weight", gpu_idx=gpu_idx)

    service_zones = polygon_zones_to_algo_zones(polygon_zones)
    service_time_fragment, service_time_start, videos_number = PoseEvent.run_service_dwell(video_paths,
                                                                        service_zones, interval=1.5, VISUAL=False)
    PoseEvent.free()

    print "service_time_fragment is {0}, service_time_start is {1}".format(service_time_fragment, service_time_start)

    return service_time_fragment, service_time_start, videos_number


def write_db(polygon_ids, video_paths, polygon_zones,gpu_idx):

    video_date = video_paths[0].split('/')[-1][-20:-9].replace('_', ' ')
    video_time = video_paths[0].split('/')[-1][-9:-4].replace('-', ':')+':00'
    print video_date
    print video_time
    video_date_time = video_date + video_time
    print "video_date_time is {0}".format(video_date_time)

    video_date_time_struct = time.strptime(video_date_time, "%Y-%m-%d %H:%M:%S")
    # timestamp_sec = time.strftime("%Y-%m-%d %H:%M:%S", timestamp)

    print video_date_time_struct
    video_date_time_sec = time.mktime(video_date_time_struct)
    print "video_date_time_sec is {0}".format(video_date_time_sec)

    # seconds -> struct time in database
    video_date_time_local = time.localtime(video_date_time_sec)
    video_date_time_database = time.strftime("%Y-%m-%d %H:%M:%S", video_date_time_local)
    print "video_date_time_database is {0}".format(video_date_time_database)

    service_time_duration, service_time_start, videos_number = checkout(video_paths, polygon_zones, gpu_idx)

    # service_time_duration = [[1], [1, 2], [5, 6, 7, 8]]
    # service_time_start = [[2], [1, 0], [1, 2, 0, 1]]

    start_time_sec = []
    end_time_sec = []

    person_in_zone = []
    for i in service_time_start:
        person_in_zone.append(len(i))

    print "person_in_zone is {0}".format(person_in_zone)

    for i, l2 in enumerate(service_time_start):
        for j in range(len(l2)):
            start_time = video_date_time_sec + l2[j]
            end_time = start_time + service_time_duration[i][j]
            start_time_sec.append(start_time)
            end_time_sec.append(end_time)
    print "start_time_sec is {0}".format(start_time_sec)
    print "end_time_sec is {0}".format(end_time_sec)

    if start_time_sec == [] and end_time_sec == []:
        print "There is no people in checkout, so i will return"
        return

    conn = connect_db.db_init()
    cursor = conn.cursor()

    i = 1
    polygon_ids_index = 0
    person_in_zone_index = 0
    date_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    dic_data = {
        "operations":
        {
            "insert":
            {
                "table": "checkout",
                "columns": ["polygon_id", "timestamp", "start_time","end_time","update_time"],
                "values": []
            }
        },
        "date_time": date_time,
        "from_process": "ad_servicetime"
    }
    for start_sec, end_sec in zip(start_time_sec, end_time_sec):

        # seconds -> struct time in database
        start_time_struct = time.localtime(start_sec)
        start_time_database = time.strftime("%Y-%m-%d %H:%M:%S", start_time_struct)
        print "start_time_database is {0}".format(start_time_database)

        end_time_struct = time.localtime(end_sec)
        end_time_database = time.strftime("%Y-%m-%d %H:%M:%S", end_time_struct)
        print "end_time_database is {0}".format(end_time_database)

        if i > person_in_zone[person_in_zone_index]:
            i = 1
            person_in_zone_index += 1
            polygon_ids_index += 1
            # i += 1
            while person_in_zone[person_in_zone_index] == 0 and person_in_zone_index != 0:
                polygon_ids_index += 1
                person_in_zone_index += 1
            polygon_id = polygon_ids[polygon_ids_index]
            i += 1
        else:
            polygon_id = polygon_ids[polygon_ids_index]
            i += 1
        if sql_model == "sql":
            insert_sql = '''INSERT INTO checkout (polygon_id, timestamp, start_time, end_time, update_time)
                    VALUES ('{polygon_id}', '{timestamp}', '{start_time}', '{end_time}', '{update_time}')'''.format(
                polygon_id=polygon_id, timestamp=video_date_time_database, start_time=start_time_database,
                end_time=end_time_database, update_time=time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))

            cursor.execute(insert_sql)
            conn.commit()
        else:
            time_now = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
            dic_data["operations"]["insert"]["values"].append([polygon_id, video_date_time_database, start_time_database,end_time_database,time_now])
    if sql_model == "sql":
        cursor.close()
        conn.close()
    else:
        json_data = json.dumps(dic_data)
        sql_data_file_path = "{}/sql_data_{}.json".format(algo_sql_folder_path,date_time)
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


