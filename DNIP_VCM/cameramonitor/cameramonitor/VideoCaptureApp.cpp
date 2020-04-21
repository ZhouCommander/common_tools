
#include <boost/filesystem.hpp>
#include "VideoCaptureApp.h"
#include "Utility.h"
#include "AppmgClient.h"
#include "Config.h"
namespace CameraMonitor
{
	VideoCaptureApp::VideoCaptureApp()
	{
		m_startTime = "2018-01-01 00:00:00";
		m_keeprun = true;
		m_runas = CONFIG.getRunas();
		m_workdir = CONFIG.getVideoCaptureWorkDir();
		m_interval = CONFIG.getCaptureInterval();
		m_extraTime = CONFIG.getBufferTime();
		boost::filesystem::path cmdPath(CONFIG.getVideoCaptureFullPath());
		std::string parentPath = cmdPath.parent_path().string();
		m_envs = "LD_LIBRARY_PATH=" + parentPath + "/lib64";
	}


	VideoCaptureApp::~VideoCaptureApp()
	{
	}

	void VideoCaptureApp::setStartTime(const long long videoLen)
	{
		LOG_INF << "setStartTime";
		std::chrono::system_clock::time_point nowTime = std::chrono::system_clock::now();
		auto totalSec = std::chrono::duration_cast<std::chrono::seconds>(nowTime - Utility::convertStr2Time(m_startTime)).count();
		if (videoLen > 0)
		{
			LOG_INF << "setStartTime videoLen <" << videoLen << "> totalSec <" << totalSec << ">.";
			auto firstCallSec = totalSec % videoLen;
			LOG_INF << "setStartTime firstCallSec <" << firstCallSec << ">.";
			std::chrono::system_clock::time_point startTime = nowTime + std::chrono::duration<int>(videoLen - firstCallSec);
			m_startTime = Utility::convertTime2Str(startTime);
			LOG_INF << "setStartTime m_startTime <" << m_startTime << ">.";
		}
		
	}
	void VideoCaptureApp::regist()
	{
		if (!isRegisted())
		{
			APPMG_CLIENT.regist(m_name, m_runas, m_cmdline, m_workdir, m_startTime,m_dailyStart,m_dailyEnd,m_envs, m_interval, m_extraTime);
		}
		
	}
	void VideoCaptureApp::unregist()
	{
		APPMG_CLIENT.unregist(m_name);
	}

	bool VideoCaptureApp::isRegisted()
	{
		return APPMG_CLIENT.isRegisted(m_name,m_runas,m_cmdline);
	}


	void VideoCaptureApp::setName(const std::string& name)
	{
		m_name = name;
	}
	std::string VideoCaptureApp::getName() const
	{
		return m_name;
	}

	void VideoCaptureApp::setCmdline(const std::string& cmdline)
	{
		m_cmdline = cmdline;
	}
	std::string VideoCaptureApp::getCmdline() const
	{
		return m_cmdline;
	}
	void VideoCaptureApp::setRunas(const std::string& runas)
	{
		m_runas = runas;
	}
	std::string VideoCaptureApp::getRunas() const
	{
		return m_runas;
	}
	void VideoCaptureApp::setWorkdir(const std::string& workdir)
	{
		m_workdir = workdir;
	}
	std::string VideoCaptureApp::getWorkdir() const
	{
		return m_workdir;
	}

	bool VideoCaptureApp::operator == (const VideoCaptureApp& app) const
	{
		const static char fname[] = "VideoCaptureApp::operator ==  ";
		LOG_INF << fname;
		return (this->m_name == app.getName() 
			&& this->m_cmdline == app.getCmdline() 
			&& this->m_runas == app.getRunas() 
			&& this->m_workdir == app.getWorkdir()
			&& this->m_dailyEnd == app.getDailyEnd()
			&& this->m_dailyStart == app.getDailyStart()
			&& this->m_envs == app.getEnv());
	}

	void VideoCaptureApp::setInterval(const int interval)
	{
		m_interval = interval;
	}
	void VideoCaptureApp::setExtraTime(const int extraTime)
	{
		m_extraTime = extraTime;
	}

	void VideoCaptureApp::setDailyStart(const std::string& dailyStart)
	{
		m_dailyStart = dailyStart;
	}
	void VideoCaptureApp::setDailyEnd(const std::string& dailyEnd)
	{
		m_dailyEnd = dailyEnd;
	}
	void VideoCaptureApp::setEnv(const std::string& env)
	{
		m_envs = env;
	}
	std::string VideoCaptureApp::getDailyStart() const
	{
		return m_dailyStart;
	}
	std::string VideoCaptureApp::getDailyEnd() const
	{
		return m_dailyEnd;
	}
	std::string VideoCaptureApp::getEnv() const
	{
		return m_envs;
	}
}
