/*******************************************************************************
* Deep North Confidential
* Copyright (C) 2018 Deep North Inc. All rights reserved.
* The source code for this program is not published
* and protected by copyright controlled
*******************************************************************************/
#ifndef APPMGCLIENT_DEFINITION
#define APPMGCLIENT_DEFINITION
#include <string>

#include <boost/serialization/singleton.hpp>
#include <cpprest/http_msg.h>
namespace CameraMonitor
{
	const static std::string APPMG_NAME = "name";
	const static std::string APPMG_CMDLINE = "command_line";
	const static std::string APPMG_RUNAS = "run_as";
	const static std::string APPMG_WORKDIR= "working_dir";
	const static std::string APPMG_ACTIVE = "active";
	const static std::string APPMG_START_TIME = "start_time";
	const static std::string APPMG_START_INTERVAL_SECONDS = "start_interval_seconds";
	const static std::string APPMG_TIMEOUT_FOR_START_INTERVAL = "start_interval_timeout";
	const static std::string APPMG_KEEP_RUNNING = "keep_running";
	const static std::string APPMG_DAILY_START = "daily_start";
	const static std::string APPMG_DAILY_END = "daily_end";
	const static std::string APPMG_DAILY_LIMITATION = "daily_limitation";
	const static std::string APPMG_ENV = "env";
	class AppmgClient :public boost::serialization::singleton<AppmgClient>
	{
	public:
		AppmgClient();
		virtual ~AppmgClient();
		void init(const std::string& ip, int port);
		bool isRegisted(
			const std::string& name,
			const std::string& runas,
			const std::string& cmdline
		);
		void regist(
			const std::string& name,
			const std::string& runas,
			const std::string& cmdline,
			const std::string& workdir,
			const std::string& startTime,
			const std::string& dailyStart,
			const std::string& dailyEnd,
			const std::string& env,
			const int interval,
			const int extraTime,
			int active = 1
		);
		void unregist(const std::string& name);
		web::json::value query();
	private:
		void httpRequest(const std::string& url, web::json::value objData, web::http::method method);
		int createToken(std::string& token);
		std::string m_appmgBaseUrl;
	};

#define APPMG_CLIENT AppmgClient::get_mutable_instance()
}

#endif

