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


algo_folder_name = 'agender'
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

# video_path = [NFS_folder + i for i in config.get('videoname')]
video_path = config.get('videoname')
print(video_path)

from face import face_analysis
from database.connect_db import db_init


# add unique repeat code 
current_dir = '{}/Algo_Bucket/{}'.format(NFS_folder,algo_folder_name)
print current_dir
#current_dir = os.path.dirname(os.path.abspath(__file__))
unique_repeat_result_path = os.path.join(current_dir, "unique_repeat_result")
if not os.path.exists(unique_repeat_result_path):
    os.mkdir(unique_repeat_result_path)

feature_file_real_time = os.path.join(unique_repeat_result_path, "real_time")
if not os.path.exists(feature_file_real_time):
    os.mkdir(feature_file_real_time)

feature_file_by_hour = os.path.join(feature_file_real_time, video_path[0].split('/')[-1][0:-7])
print feature_file_by_hour

if not os.path.exists(feature_file_by_hour):
    os.makedirs(feature_file_by_hour)

feature_file_every_video = os.path.join(feature_file_by_hour, video_path[0].split('/')[-1][0:-4] + ".txt")

print feature_file_every_video

# add unique repeat code 

fa = face_analysis(int(GPU_idx))
female_age_result, male_age_result, gender_result = fa.run_video_save(video_path[0], feature_file_every_video, 3)
fa.free()
print(female_age_result, male_age_result, gender_result)


################# jiao   Database   OP #################################


age_range = ['<20', '20-25', '25-30', '30-35', '35-40', '40-45', '45-50', '50-55', '55-60', '>60']
gender_class = ['Male', 'Female']


def get_list(result, class_list):
    obj_list = []
    print '*********************'
    for i in range(0, len(class_list)):
        print i
        if result.has_key(class_list[i]):
            obj_list.append(str(result[class_list[i]]))
        else:
            obj_list.append(str(0))
    return obj_list


def agender_database(female_age_result,male_age_result, gender_result, video_name, camid):
    ##age
    female_age_list = get_list(female_age_result, age_range)
    male_age_list = get_list(male_age_result, age_range)
    ##gender
    gender_data = get_list(gender_result, gender_class)

    # camid = video_name.split('_')[0]
    file_name = video_name.split('.')[0]
    video_time = file_name.split('_')[1] + ' ' + file_name.split('_')[2].split('-')[0] + ':' + \
                 file_name.split('_')[2].split('-')[1] + ':00'

    ##insert into database
    if sql_model == "sql":
        command = "INSERT INTO `agender` (`camera_id`, `timestamp`, `less_20`, `20_25`, `25_30`, `30_35`, `35_40`, `40_45`, `45_50`, `50_55`, `55_60`, `more_60`, `male`, `female`, `male_less_20`, `male_20_25`, `male_25_30`, `male_30_35`, `male_35_40`, `male_40_45`, `male_45_50`, `male_50_55`, `male_55_60`, `male_more_60`) " \
                "VALUES (\'" + str(camid) + "\', \'" + str(video_time) + "\', \'" + str(
            female_age_list[0]) + "\',  \'" + str(female_age_list[1]) + "\',  \'" + str(female_age_list[2]) + "\',  \'" + str(
            female_age_list[3]) + "\'," \
                        "  \'" + str(female_age_list[4]) + "\',  \'" + str(female_age_list[5]) + "\',  \'" + str(
            female_age_list[6]) + "\',  \'" + str(female_age_list[7]) + "\',  \'" + str(female_age_list[8]) + "\',  \'" + str(
            female_age_list[9]) + "\',  \'" + str(gender_data[0]) + "\',  \'" + str(gender_data[1]) + "\', \'" + str(
            male_age_list[0]) + "\',  \'" + str(male_age_list[1]) + "\',  \'" + str(male_age_list[2]) + "\',  \'" + str(
            male_age_list[3]) + "\'," \
                        "  \'" + str(male_age_list[4]) + "\',  \'" + str(male_age_list[5]) + "\',  \'" + str(
            male_age_list[6]) + "\',  \'" + str(male_age_list[7]) + "\',  \'" + str(male_age_list[8]) + "\',  \'" + str(
            male_age_list[9])+ "\')"
        print command

        conn = db_init()
        cursor = conn.cursor()
        cursor.execute(command)
        conn.commit()
        cursor.close()
        conn.close()
    else:
        date_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        dic_data = {
            "operations":
            {
                "insert":
                {
                    "table": "agender",
                    "columns": ["camera_id", 
                                "timestamp", 
                                "less_20",
                                "20_25",
                                "25_30",
                                "30_35",
                                "35_40",
                                "40_45",
                                "45_50",
                                "50_55",
                                "55_60",
                                "more_60",
                                "male",
                                "female",
                                "male_less_20",
                                "male_20_25",
                                "male_25_30",
                                "male_30_35",
                                "male_35_40",
                                "male_40_45",
                                "male_45_50",
                                "male_50_55",
                                "male_55_60",
                                "male_more_60"],
                    "values": [[str(camid),
                    str(video_time),
                    str(female_age_list[0]),
                    str(female_age_list[1]),
                    str(female_age_list[2]),
                    str(female_age_list[3]),
                    str(female_age_list[4]),
                    str(female_age_list[5]),
                    str(female_age_list[6]),
                    str(female_age_list[7]),
                    str(female_age_list[8]),
                    str(female_age_list[9]),
                    str(gender_data[0]),
                    str(gender_data[1]),
                    str(male_age_list[0]),
                    str(male_age_list[1]),
                    str(male_age_list[2]),
                    str(male_age_list[3]),
                    str(male_age_list[4]),
                    str(male_age_list[5]),
                    str(male_age_list[6]),
                    str(male_age_list[7]),
                    str(male_age_list[8]),
                    str(male_age_list[9])]]
                }
            },
            "date_time": date_time,
            "from_process": "ad_agender"
        }

        json_data = json.dumps(dic_data)
        sql_data_file_path = "{}/sql_data_{}.json".format(algo_sql_folder_path,date_time)
        try:
            with open(sql_data_file_path,'w') as f:
                f.write(json_data)
        except Exception as e:
            print e
            return False
    return True



video_name = video_path[0].split('/')[-1]
camid = config.get("cameraId")
flag = agender_database(female_age_result,male_age_result, gender_result, video_name, camid)










