/*******************************************************************************
* Deep North Confidential
* Copyright (C) 2018 Deep North Inc. All rights reserved.
* The source code for this program is not published
* and protected by copyright controlled
*******************************************************************************/
#ifndef CONFIG_DEFINITION
#define CONFIG_DEFINITION
#include <string>
#include <map>
#include <boost/serialization/singleton.hpp>
namespace CameraMonitor
{
	const static std::string CONFIG_VIDEOCAPTURE_FULLPATH = "VideoCaptureFullPath";
	const static std::string CONFIG_VIDEOCAPTURE_WORKDIR = "VideoCaptureWorkDir";
	const static std::string CONFIG_RUNAS = "Runas";
	const static std::string CONFIG_BUFFER_TIME = "BufferTime";
	const static std::string CONFIG_ERROR = "Error";
	const static std::string CONFIG_ERRORCODE = "Code";
	const static std::string CONFIG_ERRORMESSAGE = "Message";
	const static std::string CONFIG_UPDATE_INTERVAL = "UpdateInterval";
	const static std::string CONFIG_CAPTURE_INTERVAL = "CaptureInterval";
	const static std::string CONFIG_TTL = "TTL";
	const static std::string CONFIG_APPMG_PORT = "AppmgPort";
	const static std::string CONFIG_CAPTURE_INTERFACE = "CaptureInterface";
	const static std::string CONFIG_CAPTURE_PROTOCOL = "CaptureProtocol";

	const static std::string CONFIG_ALGOPARA_TABLE_NAME = "AlgoParaTableName";
	const static std::string CONFIG_ALGOPARA_ID = "AlgoParaID";
	const static std::string CONFIG_ALGOPARA_NAME = "AlgoParaName";
	const static std::string CONFIG_ALGOPARA_ALGOID = "AlgoParaAlgoID";
	const static std::string CONFIG_ALGOPARA_ALGOTYPE = "AlgoParaAlgoType";
	const static std::string CONFIG_ALGOPARA_ALGORESOLUTION = "AlgoParaAlgoResolution";
	const static std::string CONFIG_ALGOPARA_DAILY_START = "AlgoParaDailyStart";
	const static std::string CONFIG_ALGOPARA_DAILY_END = "AlgoParaDailyEnd";
	const static std::string CONFIG_ALGOPARA_CAPTURE_TYPE = "AlgoParaCaptureType";
	const static std::string CONFIG_ALGOPARA_CAPTURE_INTEVAL_SEC = "AlgoParaCaptureIntevalSec";
	const static std::string CONFIG_ALGOPARA_MEDIA_KEEP_HOURS = "AlgoParaMediaKeepHours";
	const static std::string CONFIG_ALGOPARA_PROCESS_FPS = "AlgoParaProcessFps";
	const static std::string CONFIG_ALGOPARA_MESSAGE_QUEUE_URL = "AlgoParaMessageQueueUrl";
	const static std::string CONFIG_ALGOPARA_EXTRA_PARAMETER = "AlgoParaExtraParameter";
	const static std::string CONFIG_ALGOPARA_UPLOAD_CLOUD = "AlgoParaUploadCloud";
	const static std::string CONFIG_ALGOPARA_CREATE_TIME = "AlgoParaCreateTime";

	const static std::string CONFIG_CAMERA_TABLE_NAME = "CameraTableName";
	const static std::string CONFIG_CAMERA_CAPTURE_HOST = "CameraCaptureHost";
	const static std::string CONFIG_CAMERA_NAME = "CameraName";
	const static std::string CONFIG_CAMERA_ID = "CameraID";
	const static std::string CONFIG_CAMERA_STREAM_URL = "CameraStreamUrl";
	const static std::string CONFIG_CAMERA_ALGO_PARAMETER_ID = "CameraAlgoParameterID";
	const static std::string CONFIG_CAMERA_ENABLED = "CameraEnabled";
	const static std::string CONFIG_CAMERA_CAPTURE_DIR = "CameraCaptureDir";
	const static std::string CONFIG_ALGOPARA_INSTANCE = "AlgoParaInstance";

	const static std::string CONFIG_ETCD_URLS = "EtcdUrls";

	const static std::string CONFIG_DB_MAPPING = "DBMapping";
    // wz added 
	const static std::string CONFIG_CAMERA_STATUS_ENABLED = "CaptureStatus";
	const static std::string CONFIG_REST_SCAN_PATH = "DBRestPath";

	//qzz add 
	const static std::string CONFIG_INSTANCE_ALGOID = "InstanceAlgoid";
	const static std::string CONFIG_INSTANCE_CAMERAID = "InstanceCameraid";
	const static std::string CONFIG_INSTANCE_HOSTID = "InstanceHostid";
	const static std::string CONFIG_INSTANCE_WORKTYPE = "InstanceWorktype";
	const static std::string CONFIG_INSTANCE_SCHEDULETYPE = "InstanceScheduletype";
	const static std::string CONFIG_INSTANCE_OVERRIDE_ALGOPARAMS = "InstanceOverrideAlgoparams";
	const static std::string CONFIG_INSTANCE_ENABLE = "InstanceEnable";
	const static std::string CONFIG_INSTANCE_STATUS = "InstanceStatus";

	class Config :public boost::serialization::singleton<Config>
	{
	public:
		Config();
		~Config();
		void init();
		std::string getRunas();
		std::string getVideoCaptureFullPath();
		std::string getVideoCaptureWorkDir();
		int getUpdateInterval();
		int getTtl();
		std::string getHostName();
		std::string getCaptureProtocol();
		std::string errorMsg(int errorCode);
		int getAppmgPort();
		int getBufferTime();
		int getCaptureInterval();
		std::string getCaptureInterface();
		std::string getAlgoParaTableName();
		std::string getAlgoParaID();
		std::string getAlgoParaName();
		std::string getAlgoParaAlgoID();
		std::string getAlgoParaAlgoType();
		std::string getAlgoParaAlgoResolution();
		std::string getAlgoParaDailyStart();
		std::string getAlgoParaDailyEnd();
		std::string getAlgoParaCaptureType();
		std::string getAlgoParaCaptureIntevalSec();
		std::string getAlgoParaMediaKeepHours();
		std::string getAlgoParaProcessFps();
		std::string getAlgoParaMessageQueueUrl();
		std::string getAlgoParaExtraParameter();
		std::string getAlgoParaUploadCloud();
		std::string getAlgoParaCreateTime();

		//vm_camera column name
		std::string getCameraTableName();
		std::string getCameraCaptureHost();
		std::string getCameraName();
		std::string getCameraID();
		std::string	getCameraStreamUrl();
		std::string	getCameraAlgoParameterID();
		std::string	getCameraEnabled();
		std::string getEtcdUrls();
		std::string getCameraCaptureDir();
        // wz added col name 
        std::string getCameraCaptureStatus();
        // wz added not a col name, just _dbrest.json path
        std::string getDBRestJsonPath();

		//qzz add
		std::string getAlgoParaInstance(); 
		std::string getInstanceAlgoID();
		std::string getInstanceCameraID();
		std::string getInstanceHostID();
		std::string getInstanceWorkType();
		std::string getInstanceScheduleType();
		std::string getInstanceOverrideAlgoParams();
		std::string getInstanceEnable();
		std::string getInstanceStatus();
	private:
		std::string m_runas;
		std::string m_videoCaptureFullPath;
		std::string m_videoCaptureWorkDir;
		std::string m_captureInterface;
		std::string m_captureProtocol;
		std::string m_hostName;
		int m_updateInterval;
		int m_ttl;
		std::map<int, std::string> m_mapError;
		int m_appmgPort;
		int m_bufferTime;
		int m_captureInterval;

		//vm_algo_parameter column name
		std::string m_algoParaTableName;
		std::string m_algoParaID;
		std::string m_algoParaName;
		std::string m_algoParaAlgoID;
		std::string m_algoParaAlgoType;
		std::string m_algoParaAlgoResolution;
		std::string m_algoParaDailyStart;
		std::string m_algoParaDailyEnd;
		std::string m_algoParaCaptureType;
		std::string m_algoParaCaptureIntevalSec;
		std::string m_algoParaMediaKeepHours;
		std::string m_algoParaProcessFps;
		std::string m_algoParaMessageQueueUrl;
		std::string m_algoParaExtraParameter;
		std::string m_algoParaUploadCloud;
		std::string m_algoParaCreateTime;

		//vm_camera column name
		std::string m_cameraTableName;
		std::string m_cameraCaptureHost;
		std::string m_cameraName;
		std::string m_cameraID;
		std::string	m_cameraStreamUrl;
		std::string	m_cameraAlgoParameterID;
		std::string	m_cameraEnabled;
		std::string m_cameraCaptureDir;
		std::string m_etcdUrls;                             
		// wz added the path db_rest_agent to upload all json files
		std::string m_dbrestJsonPath;

		//qzz add vm_algo_instance column name
		std::string m_algoParaInstance;
		std::string m_instanceAlgoid;
		std::string m_instanceCameraid;
		std::string m_instanceHostid;
		std::string m_instanceWorkType;
		std::string m_instanceScheduleType;
		std::string m_instanceOverrideAlgoParams;
		std::string m_instanceEnable;
		std::string m_instanceStatus;
	};b 
#define CONFIG Config::get_mutable_instance()
}

#endif

