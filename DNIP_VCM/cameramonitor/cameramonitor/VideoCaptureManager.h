/*******************************************************************************
* Deep North Confidential
* Copyright (C) 2018 Deep North Inc. All rights reserved.
* The source code for this program is not published
* and protected by copyright controlled
*******************************************************************************/
#ifndef VIDEOCAPTUREMANAGER_DEFINITION
#define VIDEOCAPTUREMANAGER_DEFINITION
#include <vector>
#include <memory>
namespace CameraMonitor
{
	class VideoCaptureApp;
	class AlgoParameter;
	class Camera;
	class Algoparainstace;
	const static std::string ETCD_CAPTURE_HOST_PATH = "/db/deepnorth/capturehost/";
	class VideoCaptureManager
	{
	public:
		VideoCaptureManager();
		virtual ~VideoCaptureManager();
		void init();
		void update();
		void updateStatus();
	private:
		bool isAllowOnThisHost(const std::string& hostname, const std::vector<std::string>& hosts);
		bool valueIsContain(std::vector<std::string>& NumArray, std::string& Num);
		bool PairvalueIsContain(std::vector<std::pair<std::string, std::string>>& PairArray,std::pair<std::string, std::string>& pair);
		void regist();
		void toApps(std::vector<std::shared_ptr<VideoCaptureApp>>& apps);
		bool isContain(std::vector<std::shared_ptr<VideoCaptureApp>>& apps, std::shared_ptr<VideoCaptureApp>& app);
		void getRegisted(std::vector<std::shared_ptr<VideoCaptureApp>>& apps);
		std::vector<std::shared_ptr<VideoCaptureApp>> m_apps;
		std::shared_ptr<AlgoParameter> m_algoParameter;
		std::shared_ptr<Camera> m_camera;
		std::shared_ptr<Algoparainstace> m_algoParaInstance;
	};
}

#endif

