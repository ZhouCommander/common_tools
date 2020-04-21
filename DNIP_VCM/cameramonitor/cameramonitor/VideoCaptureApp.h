/*******************************************************************************
* Deep North Confidential
* Copyright (C) 2018 Deep North Inc. All rights reserved.
* The source code for this program is not published
* and protected by copyright controlled
*******************************************************************************/
#ifndef VIDEOCAPTUREAPP_DEFINITION
#define VIDEOCAPTUREAPP_DEFINITION
#include <string>
namespace CameraMonitor
{
	class VideoCaptureApp
	{
	public:
		VideoCaptureApp();
		virtual ~VideoCaptureApp();
		bool isRegisted();
		void regist();
		void unregist();
		void setName(const std::string& name);
		std::string getName() const;
		void setCmdline(const std::string& cmdline);
		std::string getCmdline() const;
		void setRunas(const std::string& runas);
		std::string getRunas() const;
		void setWorkdir(const std::string& workdir);
		std::string getWorkdir() const;
		void setInterval(const int interval);
		void setExtraTime(const int extraTime);
		void setDailyStart(const std::string& dailyStart);
		void setDailyEnd(const std::string& dailyEnd);
		void setEnv(const std::string& env);
		//video length default is 300s
		void setStartTime(const long long videoLen);
		std::string getDailyStart() const;
		std::string getDailyEnd() const;
		std::string getEnv() const;
		bool operator == (const VideoCaptureApp& app) const;
	private:
		std::string m_name;
		std::string m_cmdline;
		std::string m_runas;
		std::string m_workdir;
		std::string m_startTime;
		std::string m_dailyStart;
		std::string m_dailyEnd;
		std::string m_envs;
		int m_interval;
		int m_extraTime;
		bool m_keeprun;

	};
}

#endif

