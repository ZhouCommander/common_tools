#include <algorithm>

#include "VideoCaptureManager.h"
#include "AlgoParameter.h"
#include "Algoparainstace.h"
#include "Camera.h"
#include "VideoCaptureApp.h"
#include "Utility.h"
#include "AppmgClient.h"
#include "ETCDWrapper.h"
#include "Config.h"

#include<string>
#include<vector>

namespace CameraMonitor
{
	VideoCaptureManager::VideoCaptureManager()
	{
	}


	VideoCaptureManager::~VideoCaptureManager()
	{
	}

	void VideoCaptureManager::init()
	{
		const static char fname[] = "VideoCaptureManager::init  ";
		LOG_INF << fname;
		m_apps.clear();
		m_algoParameter = std::make_shared<AlgoParameter>();
		m_camera = std::make_shared<Camera>();
		m_algoParaInstance = std::make_shared<Algoparainstace>();
		getRegisted(m_apps);
		LOG_INF << "m_apps size <" << m_apps.size() << ">." ;

	}

	void VideoCaptureManager::update()
	{
		const static char fname[] = "VideoCaptureManager::update()  ";
		LOG_INF << fname;
		m_algoParameter->update();
		m_camera->update();
		m_algoParaInstance->update();
		std::vector<std::shared_ptr<VideoCaptureApp>> apps;
		apps.clear();
		toApps(apps);
		LOG_INF << "apps size <" << apps.size() << ">.";
		auto app = apps.begin();
		while (app != apps.end())
		{
			bool exist = false;
			auto a = m_apps.begin();
			while (a != m_apps.end())
			{
				LOG_INF << "app <" << (*a)->getName() << ">.";
				//already registed
				if (**a == **app)
				{
					LOG_INF << "app <" << (*app)->getName() << "> alread exist.";
					exist = true;
					break;
				}
				else
				{
					//db item modified,update it to appmg
					if ((*a)->getName() == (*app)->getName())
					{
						LOG_WAR << "modify app <" << (*app)->getName() << ">." ;
						exist = true;
						(*a)->unregist();
						(*app)->regist();
						(*a)->setCmdline((*app)->getCmdline());
						(*a)->setWorkdir((*app)->getWorkdir());
						(*a)->setRunas((*app)->getRunas());
						break;
					}
				}
				++a;				
			}

			if (!exist)
			{
				LOG_WAR << "add app <" << (*app)->getName() << ">.";
				m_apps.push_back(*app);
				(*app)->regist();
			}
			++app;
		}

		//unreg app when not in db
		auto appRegisted = m_apps.begin();
		while (appRegisted != m_apps.end())
		{
			if (!isContain(apps, *appRegisted))
			{
				LOG_WAR << "remove app <" << (*appRegisted)->getName() << ">.";
				(*appRegisted)->unregist();
				appRegisted = m_apps.erase(appRegisted);
			}
			else
			{
				++appRegisted;
			}
		}
		updateStatus();
	}

	void VideoCaptureManager::toApps(std::vector<std::shared_ptr<VideoCaptureApp>>& apps)
	{
		const static char fname[] = "VideoCaptureManager::fromEtcd  ";
		LOG_INF << fname;
		std::vector<std::map<std::string, std::string>> algoParameterList = m_algoParameter->getData();
		std::vector<std::map<std::string, std::string>> cameraList = m_camera->getData();
		std::vector<std::map<std::string, std::string>> algoParaInstanceList = m_algoParaInstance->getData();
		//todo qzz 
		LOG_INF << "cameraList size <" << cameraList.size() << ">." ;
		LOG_INF << "algoParameterList size <" << algoParameterList.size() << ">." ;
		LOG_INF << "algoParaInstanceList size" << algoParaInstanceList.size() << ">.";

		std::string captureProtocol = CONFIG.getCaptureProtocol();
		if (!apps.empty())
		{
			apps.clear();
		}

		for (auto camera = cameraList.begin(); camera != cameraList.end(); ++camera)
		{
			std::string cameraId = camera->at(CONFIG.getCameraID());
			
			std::vector<std::string> hosts;
			Utility::splitString(camera->at(CONFIG.getCameraCaptureHost()), hosts, ",");
			if ( isAllowOnThisHost(CONFIG.getHostName(),hosts) && "1" == camera->at(CONFIG.getCameraEnabled()))
			{
                // wz added 2019-03-07 14:04:28 capture_status is enabled or not
                bool capStatus = false;
				// jiao added 2019-08-29 11:38:00 realtime and video capture are enable or not
				bool rtspVideo = false;
                // extraparam default is None
                std::string extraParam = camera->at(CONFIG.getAlgoParaExtraParameter());
                // wz added parse extraParam find 'capture_status' key
                if (extraParam != "None")
                {
                    if (extraParam.find("realtimeprocess=on") != std::string::npos)
                    {
                        // skip the real time process
                        LOG_INF << "find realtimeprocess, skipped";
                        continue;
                    }
                    capStatus = (extraParam.find("capturestatus=on") != std::string::npos);
					rtspVideo = (extraParam.find("realtimevideo=on") != std::string::npos);
					LOG_INF << "RTSPVIDEO:<" << rtspVideo << ">.";
                }
				std::shared_ptr<VideoCaptureApp> app = std::make_shared<VideoCaptureApp>();
				std::string cameraName = camera->at(CONFIG.getCameraName());
				LOG_INF << "name <" << cameraName << ">.";
				app->setName("camera_" + cameraId);
				std::string cameraStreamUrl = camera->at(CONFIG.getCameraStreamUrl());
				std::string cameraAlgoParameterId = camera->at(CONFIG.getCameraAlgoParameterID());
				std::string captureDir = camera->at(CONFIG.getCameraCaptureDir());

				for (auto algoparainstance = algoParaInstanceList.begin(); algoparainstance != algoParaInstanceList.end(); ++algoparainstance)
				{
					std::string instanceAlgoid = algoparainstance->at(CONFIG.getInstanceAlgoID());
					std::string instanceCameraid = algoparainstance->at(CONFIG.getInstanceCameraID());
					std::string instanceHostid = algoparainstance->at(CONFIG.getInstanceHostID());
					std::string instanceWorkType = algoparainstance->at(CONFIG.getInstanceWorkType());
					std::string instanceScheduleType = algoparainstance->at(CONFIG.getInstanceScheduleType());
					std::string instanceOverrideAlgoParams = algoparainstance->at(CONFIG.getInstanceOverrideAlgoParams());
					std::string instanceEnable = algoparainstance->at(CONFIG.getInstanceEnable());
					std::string instanceStatus = algoparainstance->at(CONFIG.getInstanceStatus());

					std::vector<std::string> NumArray;
					Utility::splitString(instanceCameraid, NumArray, ",");
					if (valueIsContain(NumArray, cameraId))
					{
						for (auto algoParameter = algoParameterList.begin(); algoParameter != algoParameterList.end(); ++algoParameter)
						{
							if (algoParameter->at(CONFIG.getAlgoParaID()) == instanceAlgoid)
							{
								std::string	messageQueueUrl = algoParameter->at(CONFIG.getAlgoParaMessageQueueUrl());
								std::string	captureType = algoParameter->at(CONFIG.getAlgoParaCaptureType());
								std::string	captureIntevalSec = algoParameter->at(CONFIG.getAlgoParaCaptureIntevalSec());
								std::string	algoName = algoParameter->at(CONFIG.getAlgoParaName());
								std::string	dailyStart = algoParameter->at(CONFIG.getAlgoParaDailyStart());
								std::string	dailyEnd = algoParameter->at(CONFIG.getAlgoParaDailyEnd());
								//qzz update

								std::vector<std::pair<std::string, std::string>> cpTypeIntervalList;
								std::pair<std::string, std::string> Pair; 
								Pair = std::pair<std::string, std::string>(captureType, captureIntevalSec);
								if (!PairvalueIsContain(cpTypeIntervalList, Pair))
								{
									std::string cmdline = CONFIG.getVideoCaptureFullPath();
									cmdline.append(" ");
									cmdline.append("-c");
									cmdline.append(" \"");
									cmdline.append(cameraStreamUrl);
									cmdline.append("\" ");
									cmdline.append("-u");
									cmdline.append(" ");
									cmdline.append(cameraId);
									cmdline.append(" ");
									cmdline.append("-q");
									cmdline.append(" \"");
									cmdline.append(messageQueueUrl);
									cmdline.append("\" ");
									cmdline.append("-t");
									cmdline.append(" ");
									cmdline.append(captureType);
									cmdline.append(" ");
									cmdline.append("-i");
									cmdline.append(" ");
									cmdline.append(captureIntevalSec);
									cmdline.append(" ");
									cmdline.append("-d");
									cmdline.append(" ");
									cmdline.append(captureDir);
									cmdline.append(" ");
									cmdline.append("-p");
									cmdline.append(" ");
									cmdline.append(CONFIG.getCaptureInterface());
									cmdline.append(" ");
									cmdline.append("-e");
									cmdline.append(" ");;
									cmdline.append(std::to_string(CONFIG.getCaptureInterval()));
									cmdline.append(" ");
									cmdline.append("-n");
									cmdline.append(" \"");
									cmdline.append(algoName);
									cmdline.append("\"");             
									if (capStatus)
									{
										// wz added capture status is opened 
										cmdline.append(" ")
											.append("-j")
											.append(" \"")
											.append(CONFIG.getDBRestJsonPath())
											.append("\" ");
									}

									if (rtspVideo)
									{
										//jiao added the realtime and capture video staus are opened which cannot send MQ
										cmdline.append(" ")
											.append("-k")
											.append(" \"")
											.append("realtimevideo")
											.append("\" ");
									}
									if (!captureProtocol.empty())
									{
										cmdline.append(" -r ");
										cmdline.append(captureProtocol);
									}
									LOG_INF << "cmdline <" << cmdline;
									app->setCmdline(cmdline);
									if (dailyStart != "None" && dailyEnd != "None")
									{
										app->setDailyStart(dailyStart);
										app->setDailyEnd(dailyEnd);
									}			

									if (cameraStreamUrl.empty() || algoName.empty() || captureDir.empty() || captureIntevalSec.empty() || messageQueueUrl.empty())
									{
										LOG_ERR << "camera <" << cameraId << "> invalid parameter.";
									}
									else
									{
										std::string::size_type sz;   // alias of size_t
										int videoLen = std::stoi(captureIntevalSec, &sz);
										app->setStartTime(videoLen);
										apps.push_back(app);
									}
									cpTypeIntervalList.push_back(std::pair<std::string, std::string>(captureType, captureIntevalSec));
								}

								break;
							}
						}
					}

				}			
               	
				
			}

		}
	}
	void VideoCaptureManager::regist()
	{
		const static char fname[] = "VideoCaptureManager::regist()  ";
		LOG_INF << fname;
		for_each(m_apps.begin(), m_apps.end(), [](std::vector<std::shared_ptr<VideoCaptureApp>>::reference app) {app->regist(); });
	}

	bool VideoCaptureManager::isContain(std::vector<std::shared_ptr<VideoCaptureApp>>& apps, std::shared_ptr<VideoCaptureApp>& app)
	{
		const static char fname[] = "VideoCaptureManager::isContain  ";
		LOG_INF << fname;
		auto iter = apps.begin();
		while (iter != apps.end())
		{
			if (**iter == *app)
			{
				LOG_INF << "contain name <" << app->getName() << ">.";
				return true;
			}
			++iter;
		}
		LOG_INF << "not contain name <" << app->getName() << ">.";
		return false;
	}

	//qzz add 
	bool VideoCaptureManager::valueIsContain(std::vector<std::string>& NumArray, std::string& Num){
		const static char fname[] = "VideoCaptureManager::valueIsContain  ";
		LOG_INF << fname;
		int count = NumArray.size();
		for (int i = 0; i < count; i++)
		{
			if ((NumArray.at(i) == Num){
				LOG_INF << "value contained <" << Num << ">.";
				return true;
			}
		}
		return false;
	}

	bool VideoCaptureManager::PairvalueIsContain(std::vector<std::pair<std::string, std::string>>& PairArray, std::pair<std::string, std::string>& pair)){
		const static char fname[] = "VideoCaptureManager::PairvalueIsContain  ";
		std::string capturetype;
		std::string captureinterval;
		LOG_INF << fname;
		auto iter = PairArray.begin();
		while (iter != PairArray.end())
		{
			if (iter->first == pair->first && iter->second == pair->second)
			{
				capturetype = iter->first;
				captureinterval = iter->second;
				LOG_INF << "value contained <" << capturetype << ">.";
				return true;
			}
			++iter;
		}
		capturetype = pair->first;
		captureinterval = pair->second;
		LOG_INF << "value not contained" << capturetype << ">.";
		return false;
	}

	void  VideoCaptureManager::getRegisted(std::vector<std::shared_ptr<VideoCaptureApp>>& apps)
	{
		const static char fname[] = "VideoCaptureManager::getRegisted  ";
		LOG_INF << fname;
		auto obj = APPMG_CLIENT.query();
		auto arr = obj.as_array();
		for (auto iter = arr.begin(); iter != arr.end(); iter++)
		{
			auto jobj = iter->as_object();
			auto cmdline = GET_JSON_STR_VALUE(jobj, APPMG_CMDLINE);
			LOG_INF << "cmdline <" << cmdline << ">.";
			//start with "/opt/videocapture"
			if (0 == cmdline.find(CONFIG.getVideoCaptureFullPath()))
			{
				auto app = std::make_shared<VideoCaptureApp>();
				app->setCmdline(cmdline);
				app->setName(GET_JSON_STR_VALUE(jobj, APPMG_NAME));
				app->setRunas(GET_JSON_STR_VALUE(jobj, APPMG_RUNAS));
				apps.push_back(app);
			}
		}
	}
	void VideoCaptureManager::updateStatus()
	{
		const static char fname[] = "VideoCaptureManager::updateStatus()  ";
		LOG_INF << fname;
		auto obj = APPMG_CLIENT.query();
		auto arr = obj.as_array();
		for (auto iter = arr.begin(); iter != arr.end(); iter++)
		{
			auto jobj = iter->as_object();
			auto cmdline = GET_JSON_STR_VALUE(jobj, APPMG_CMDLINE);
			LOG_INF << "cmdline <" << cmdline << ">.";
			//start with "/opt/videocapture"
			if (0 == cmdline.find(CONFIG.getVideoCaptureFullPath()))
			{

				std::string appName = GET_JSON_STR_VALUE(jobj, APPMG_NAME);
				const static std::string appNamePre = "camera_";
				auto appNameLen = appName.length();
				auto appNamePreLen = appNamePre.length();
				if (0 == appName.find(appNamePre) && appNameLen > appNamePreLen)
				{
					std::string cameraID = appName.substr(appNamePre.length(), appNameLen - appNamePreLen);
					ETCD_WRAPPER.set(ETCD_CAPTURE_HOST_PATH + CONFIG.getHostName() + "/" + cameraID +"/status", CONFIG.errorMsg(GET_JSON_INT_VALUE(jobj, "return")), CONFIG.getTtl());
				}
				
			}
		}
	}

	bool VideoCaptureManager::isAllowOnThisHost(const std::string& hostname, const std::vector<std::string>& hosts)
	{
		const static char fname[] = "VideoCaptureManager::IsAllowOnThisHost";
		LOG_INF << fname;
		LOG_INF << "hostname <" << hostname << ">.";
		LOG_INF << "hosts.size <" << hosts.size() << ">.";
		if (hosts.empty())
		{
			return false;
		}
		//first host 
		if (hosts.at(0) == hostname)
		{
			return true;
		}
		std::size_t index = 0;
		auto bFind = false;
		for (; index < hosts.size(); index++)
		{
			if (hosts.at(index) == hostname)
			{
				//in the capture hosts
				bFind = true;
				break;
			}
		}

		if (bFind)
		{
			//not the first host. 
			for (int i = 0; i < index; i++)
			{
				if (ETCD_WRAPPER.isKeyExist(ETCD_CAPTURE_HOST_PATH + hosts.at(i)))
				{
					//if there is a host before it online again.do not allow on this host.
					return false;
				}
			}
			//there is no online host before this one ,use it.
			return true;
		}
		else
		{
			//not in host list.
			return false;
		}
	}
}



