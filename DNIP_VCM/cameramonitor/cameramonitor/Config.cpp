/*******************************************************************************
* Deep North Confidential
* Copyright (C) 2018 Deep North Inc. All rights reserved.
* The source code for this program is not published
* and protected by copyright controlled
*******************************************************************************/
#include <fstream>
#include <boost/asio/ip/host_name.hpp>
#include <cpprest/json.h>
#include "Config.h"
#include "Utility.h"
#include "Camera.h"
#include "AlgoParameter.h"
namespace CameraMonitor
{
	Config::Config()
	{
		m_updateInterval = 10;
		m_ttl = 30;
		m_appmgPort = 5050;
		m_bufferTime = 0;
		m_captureInterval = 3600;
	}


	Config::~Config()
	{
	}

	void Config::init()
	{
		const static char fname[] = " Config::init()  ";
		LOG_INF << fname;
		web::json::value jsonValue;
		std::string jsonPath = Utility::getSelfFullPath() + ".json";
		std::ifstream jsonFile(jsonPath);
		if (!jsonFile.is_open())
		{
			LOG_ERR << "ERROR can not open configuration file <" << jsonPath << ">";
		}
		else
		{
			std::string str((std::istreambuf_iterator<char>(jsonFile)), std::istreambuf_iterator<char>());
			jsonFile.close();
			LOG_INF << "Config <" << str << ">.";
			auto jval = web::json::value::parse(GET_STRING_T(str));
			web::json::object jobj = jval.as_object();
			m_videoCaptureFullPath = GET_JSON_STR_VALUE(jobj, CONFIG_VIDEOCAPTURE_FULLPATH);
			m_videoCaptureWorkDir = GET_JSON_STR_VALUE(jobj, CONFIG_VIDEOCAPTURE_WORKDIR);
			m_captureInterface = GET_JSON_STR_VALUE(jobj, CONFIG_CAPTURE_INTERFACE);
			m_runas = GET_JSON_STR_VALUE(jobj, CONFIG_RUNAS);
			m_updateInterval = GET_JSON_INT_VALUE(jobj, CONFIG_UPDATE_INTERVAL);
			m_ttl = GET_JSON_INT_VALUE(jobj, CONFIG_TTL);
			m_appmgPort = GET_JSON_INT_VALUE(jobj, CONFIG_APPMG_PORT);
			m_bufferTime = GET_JSON_INT_VALUE(jobj, CONFIG_BUFFER_TIME);
			m_captureInterval = GET_JSON_INT_VALUE(jobj, CONFIG_CAPTURE_INTERVAL);
			m_etcdUrls = GET_JSON_STR_VALUE(jobj, CONFIG_ETCD_URLS);
			m_captureProtocol = GET_JSON_STR_VALUE(jobj, CONFIG_CAPTURE_PROTOCOL);
			// wz added _dbrest.json path
			m_dbrestJsonPath = GET_JSON_STR_VALUE(jobj, CONFIG_REST_SCAN_PATH);

			m_mapError.clear();
			auto& jArr = jobj.at(GET_STRING_T(CONFIG_ERROR)).as_array();
			for (auto iter = jArr.begin(); iter != jArr.end(); ++iter)
			{
				auto jsonObj = iter->as_object();
				m_mapError.insert(std::pair<int, std::string>(GET_JSON_INT_VALUE(jsonObj, CONFIG_ERRORCODE), GET_JSON_STR_VALUE(jsonObj, CONFIG_ERRORMESSAGE)));
			}
			auto objDBMapping = jobj.at(GET_STRING_T(CONFIG_DB_MAPPING)).as_object();
			m_algoParaTableName = GET_JSON_STR_VALUE(objDBMapping, CONFIG_ALGOPARA_TABLE_NAME);
			LOG_INF << "m_algoParaTableName <" << m_algoParaTableName << ">.";
			m_algoParaID = GET_JSON_STR_VALUE(objDBMapping, CONFIG_ALGOPARA_ID);
			LOG_INF << "m_algoParaID <" << m_algoParaID << ">.";
			m_algoParaName = GET_JSON_STR_VALUE(objDBMapping, CONFIG_ALGOPARA_NAME);
			LOG_INF << "m_algoParaName <" << m_algoParaName << ">.";
			m_algoParaAlgoID = GET_JSON_STR_VALUE(objDBMapping, CONFIG_ALGOPARA_ALGOID);
			LOG_INF << "m_algoParaAlgoID <" << m_algoParaAlgoID << ">.";
			m_algoParaAlgoType = GET_JSON_STR_VALUE(objDBMapping, CONFIG_ALGOPARA_ALGOTYPE);
			LOG_INF << "m_algoParaAlgoType <" << m_algoParaAlgoType << ">.";
			m_algoParaAlgoResolution = GET_JSON_STR_VALUE(objDBMapping, CONFIG_ALGOPARA_ALGORESOLUTION);
			LOG_INF << "m_algoParaAlgoResolution <" << m_algoParaAlgoResolution << ">.";
			m_algoParaDailyStart = GET_JSON_STR_VALUE(objDBMapping, CONFIG_ALGOPARA_DAILY_START);
			LOG_INF << "m_algoParaDailyStart <" << m_algoParaDailyStart << ">.";
			m_algoParaDailyEnd = GET_JSON_STR_VALUE(objDBMapping, CONFIG_ALGOPARA_DAILY_END);
			LOG_INF << "m_algoParaDailyEnd <" << m_algoParaDailyEnd << ">.";
			m_algoParaCaptureType = GET_JSON_STR_VALUE(objDBMapping, CONFIG_ALGOPARA_CAPTURE_TYPE);
			LOG_INF << "m_algoParaCaptureType <" << m_algoParaCaptureType << ">.";
			m_algoParaCaptureIntevalSec = GET_JSON_STR_VALUE(objDBMapping, CONFIG_ALGOPARA_CAPTURE_INTEVAL_SEC);
			LOG_INF << "m_algoParaCaptureIntevalSec <" << m_algoParaCaptureIntevalSec << ">.";
			m_algoParaMediaKeepHours = GET_JSON_STR_VALUE(objDBMapping, CONFIG_ALGOPARA_MEDIA_KEEP_HOURS);
			LOG_INF << "m_algoParaMediaKeepHours <" << m_algoParaMediaKeepHours << ">.";
			m_algoParaProcessFps = GET_JSON_STR_VALUE(objDBMapping, CONFIG_ALGOPARA_PROCESS_FPS);
			LOG_INF << "m_algoParaProcessFps <" << m_algoParaProcessFps << ">.";
			m_algoParaMessageQueueUrl = GET_JSON_STR_VALUE(objDBMapping, CONFIG_ALGOPARA_MESSAGE_QUEUE_URL);
			LOG_INF << "m_algoParaMessageQueueUrl <" << m_algoParaMessageQueueUrl << ">.";
			m_algoParaExtraParameter = GET_JSON_STR_VALUE(objDBMapping, CONFIG_ALGOPARA_EXTRA_PARAMETER);
			LOG_INF << "m_algoParaExtraParameter <" << m_algoParaExtraParameter << ">.";
			m_algoParaUploadCloud = GET_JSON_STR_VALUE(objDBMapping, CONFIG_ALGOPARA_UPLOAD_CLOUD);
			LOG_INF << "m_algoParaUploadCloud <" << m_algoParaUploadCloud << ">.";
			m_algoParaCreateTime = GET_JSON_STR_VALUE(objDBMapping, CONFIG_ALGOPARA_CREATE_TIME);
			LOG_INF << "m_algoParaCreateTime <" << m_algoParaCreateTime << ">.";

			m_cameraTableName = GET_JSON_STR_VALUE(objDBMapping, CONFIG_CAMERA_TABLE_NAME);
			LOG_INF << "m_cameraTableName <" << m_cameraTableName << ">.";
			
			m_algoParaInstance = GET_JSON_STR_VALUE(objDBMapping, CONFIG_ALGOPARA_INSTANCE);
			LOG_INF << "m_algoParaInstance <" << m_algoParaInstance << ">.";
			
			m_cameraCaptureHost = GET_JSON_STR_VALUE(objDBMapping, CONFIG_CAMERA_CAPTURE_HOST);
			LOG_INF << "m_cameraCaptureHost <" << m_cameraCaptureHost << ">.";
			m_cameraName = GET_JSON_STR_VALUE(objDBMapping, CONFIG_CAMERA_NAME);
			LOG_INF << "m_cameraName <" << m_cameraName << ">.";
			m_cameraID = GET_JSON_STR_VALUE(objDBMapping, CONFIG_CAMERA_ID);
			LOG_INF << "m_cameraID <" << m_cameraID << ">." ;
			m_cameraStreamUrl = GET_JSON_STR_VALUE(objDBMapping, CONFIG_CAMERA_STREAM_URL);
			LOG_INF << "m_cameraStreamUrl <" << m_cameraStreamUrl << ">.";
			m_cameraAlgoParameterID = GET_JSON_STR_VALUE(objDBMapping, CONFIG_CAMERA_ALGO_PARAMETER_ID);
			LOG_INF << "m_cameraAlgoParameterID <" << m_cameraAlgoParameterID << ">.";
			m_cameraEnabled = GET_JSON_STR_VALUE(objDBMapping, CONFIG_CAMERA_ENABLED);
			LOG_INF << "m_cameraEnabled <" << m_cameraEnabled << ">.";
			m_cameraCaptureDir = GET_JSON_STR_VALUE(objDBMapping, CONFIG_CAMERA_CAPTURE_DIR);
			LOG_INF << "m_cameraCaptureDir <" << m_cameraCaptureDir << ">.";

			m_instanceAlgoid = GET_JSON_STR_VALUE(objDBMapping, CONFIG_INSTANCE_ALGOID);
			LOG_INF << "m_instanceAlgoid <" << m_instanceAlgoid << ">.";
			m_instanceCameraid = GET_JSON_STR_VALUE(objDBMapping, CONFIG_INSTANCE_CAMERAID);
			LOG_INF << "m_instanceCameraid <" << m_instanceCameraid << ">.";
			m_instanceHostid = GET_JSON_STR_VALUE(objDBMapping, CONFIG_INSTANCE_HOSTID);
			LOG_INF << "m_instanceHostid <" << m_instanceHostid << ">.";
			m_instanceWorkType = GET_JSON_STR_VALUE(objDBMapping, CONFIG_INSTANCE_WORKTYPE);
			LOG_INF << "m_instanceWorkType <" << m_instanceWorkType << ">.";
			m_instanceScheduleType = GET_JSON_STR_VALUE(objDBMapping, CONFIG_INSTANCE_SCHEDULETYPE);
			LOG_INF << "m_instanceScheduleType <" << m_instanceScheduleType << ">.";
			m_instanceOverrideAlgoParams = GET_JSON_STR_VALUE(objDBMapping, CONFIG_INSTANCE_OVERRIDE_ALGOPARAMS);
			LOG_INF << "m_instanceOverrideAlgoParams <" << m_instanceOverrideAlgoParams << ">.";
			m_instanceEnable = GET_JSON_STR_VALUE(objDBMapping, CONFIG_INSTANCE_ENABLE);
			LOG_INF << "m_instanceEnable <" << m_instanceEnable << ">.";
			m_instanceStatus = GET_JSON_STR_VALUE(objDBMapping, CONFIG_INSTANCE_STATUS);
			LOG_INF << "m_instanceStatus <" << m_instanceStatus << ">.";
			
		}
		LOG_INF << "m_videoCaptureFullPath <" << m_videoCaptureFullPath << ">.";
		LOG_INF << "m_videoCaptureWorkDir <" << m_videoCaptureWorkDir << ">.";
		LOG_INF << "m_runas <" << m_runas << ">.";
		LOG_INF << "m_updateInterval <" << m_updateInterval << ">.";
		LOG_INF << "m_ttl <" << m_ttl << ">.";
		LOG_INF << "m_appmgPort <" << m_appmgPort << ">.";
		LOG_INF << "m_bufferTime <" << m_bufferTime << ">.";
		LOG_INF << "m_captureInterval <" << m_captureInterval << ">.";
		LOG_INF << "m_mapError size <" << m_mapError.size() << ">.";
		m_hostName = boost::asio::ip::host_name();

	}
	std::string Config::getRunas()
	{
		return m_runas;
	}
	std::string Config::getVideoCaptureFullPath()
	{
		return m_videoCaptureFullPath;
	}
	std::string Config::getVideoCaptureWorkDir()
	{
		return m_videoCaptureWorkDir;
	}
	int Config::getUpdateInterval()
	{
		return m_updateInterval;
	}
	int Config::getTtl()
	{
		return m_ttl;
	}
 
	std::string Config::getHostName()
	{
		return m_hostName;
	}

	std::string Config::getCaptureProtocol()
	{
		return m_captureProtocol;
	}

	int Config::getAppmgPort()
	{
		return m_appmgPort;
	}
	int Config::getBufferTime()
	{
		return m_bufferTime;
	}
	int Config::getCaptureInterval()
	{
		return m_captureInterval;
	}

	std::string Config::errorMsg(int errorCode)
	{
		std::string message;
		if (m_mapError.count(errorCode) > 0)
		{
			message = m_mapError.at(errorCode);
		}
		else
		{
			message = "Unknow error";
		}
		return message;
	}

	std::string Config::getCaptureInterface()
	{
		return m_captureInterface;
	}

	std::string  Config::getAlgoParaTableName()
	{
		return m_algoParaTableName;
	}
	std::string Config::getAlgoParaID()
	{
		return m_algoParaID;
	}
	std::string Config::getAlgoParaName()
	{
		return m_algoParaName;
	}
	std::string Config::getAlgoParaAlgoID()
	{
		return m_algoParaAlgoID;
	}
	std::string Config::getAlgoParaAlgoType()
	{
		return m_algoParaAlgoType;
	}
	std::string Config::getAlgoParaAlgoResolution()
	{
		return m_algoParaAlgoResolution;
	}
	std::string Config::getAlgoParaDailyStart()
	{
		return m_algoParaDailyStart;
	}
	std::string Config::getAlgoParaDailyEnd()
	{
		return m_algoParaDailyEnd;
	}
	std::string Config::getAlgoParaCaptureType()
	{
		return m_algoParaCaptureType;
	}
	std::string Config::getAlgoParaCaptureIntevalSec()
	{
		return m_algoParaCaptureIntevalSec;
	}
	std::string Config::getAlgoParaMediaKeepHours()
	{
		return m_algoParaMediaKeepHours;
	}

	std::string Config::getAlgoParaProcessFps()
	{
		return m_algoParaProcessFps;
	}
	std::string Config::getAlgoParaMessageQueueUrl()
	{
		return m_algoParaMessageQueueUrl;
	}
	std::string Config::getAlgoParaExtraParameter()
	{
		return m_algoParaExtraParameter;
	}
	std::string Config::getAlgoParaUploadCloud()
	{
		return m_algoParaUploadCloud;
	}
	std::string Config::getAlgoParaCreateTime()
	{
		return m_algoParaCreateTime;
	}

	//vm_camera column name
	std::string Config::getCameraTableName()
	{
		return m_cameraTableName;
	}
	//vm_para_instance column name
	std::string Config::getAlgoParaInstance()
	{
		return m_algoParaInstance;
	}
	std::string Config::getCameraCaptureHost()
	{
		return m_cameraCaptureHost;
	}
	std::string Config::getCameraName()
	{
		return m_cameraName;
	}
	std::string Config::getCameraID()
	{
		return m_cameraID;
	}
	std::string	Config::getCameraStreamUrl()
	{
		return m_cameraStreamUrl;
	}
	std::string	Config::getCameraAlgoParameterID()
	{
		return m_cameraAlgoParameterID;
	}
	std::string	Config::getCameraEnabled()
	{
		return m_cameraEnabled;
	}

	std::string Config::getCameraCaptureDir()
	{
		return m_cameraCaptureDir;
	}

	std::string Config::getDBRestJsonPath()
	{
		return m_dbrestJsonPath;
	}

	std::string Config::getEtcdUrls()
	{
		return m_etcdUrls;
	}

	std::string Config::getInstanceAlgoID()
	{
		return m_instanceAlgoid;
	}

	std::string Config::getInstanceCameraID()
	{
		return m_instanceCameraid;
	}
	std::string Config::getInstanceHostID()
	{
		return m_instanceHostid;
	}
	std::string Config::getInstanceWorkType()
	{
		return m_instanceWorkType;
	}
	std::string Config::getInstanceScheduleType()
	{
		return m_instanceScheduleType;
	}
	std::string Config::getInstanceOverrideAlgoParams()
	{
		return m_instanceOverrideAlgoParams;
	}
	std::string Config::getInstanceEnable()
	{
		return m_instanceEnable;
	}
	std::string Config::getInstanceStatus()
	{
		return m_instanceStatus;
	}
}
