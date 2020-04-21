/*******************************************************************************
* Deep North Confidential
* Copyright (C) 2018 Deep North Inc. All rights reserved.
* The source code for this program is not published
* and protected by copyright controlled
*******************************************************************************/
#include "Utility.h"
#include <string>
#include <map>
#include <fstream>
#include <iostream>
#include <stdio.h>
#include <algorithm>
#include <cctype>
#include <stdlib.h>
#include <stdio.h>
#if	!defined(WIN32)
#include <dirent.h>
#include <sys/stat.h>
#include <errno.h>
#include <pwd.h>
#endif
#include <iomanip>

#include <log4cpp/Category.hh>
#include <log4cpp/Appender.hh>
#include <log4cpp/FileAppender.hh>
#include <log4cpp/Priority.hh>
#include <log4cpp/PatternLayout.hh>
#include <log4cpp/RollingFileAppender.hh>
#include <log4cpp/OstreamAppender.hh>
using namespace log4cpp;

using namespace std;

Utility::Utility()
{
}


Utility::~Utility()
{
}


bool Utility::isNumber(string s)
{
	return !s.empty() && std::find_if(s.begin(), s.end(), [](char c) { return !std::isdigit(c); }) == s.end();
}

void Utility::stringReplace(std::string & strBase, const std::string strSrc, const std::string strDst)
{
	std::string::size_type position = 0;
	std::string::size_type srcLen = strSrc.size();
	std::string::size_type dstLen = strDst.size();

	while ((position = strBase.find(strSrc, position)) != std::string::npos)
	{
		strBase.replace(position, srcLen, strDst);
		position += dstLen;
	}
}

std::string Utility::stdStringTrim(const std::string & str)
{
	char *line = const_cast <char *> (str.c_str());
	// trim the line on the left and on the right
	size_t len = str.length();
	size_t start = 0;
	while (isspace(*line))
	{
		++line;
		--len;
		++start;
	}
	while (len > 0 && isspace(line[len - 1]))
	{
		--len;
	}
	return len >= start ? str.substr(start, len) : str.substr(start);
}

std::string Utility::getSelfFullPath()
{
	#define MAXBUFSIZE 1024
	int count = 0;
	char buf[MAXBUFSIZE] = { 0 };
#if	!defined(WIN32)
	count = readlink("/proc/self/exe", buf, MAXBUFSIZE);
#endif
	if (count < 0 || count >= MAXBUFSIZE)
	{
		printf("Failed\n");
		return buf;
	}
	else
	{
		buf[count] = '\0';
		return buf;
	}
}

void SignalHandle(const char* data, int size)
{
	std::string str = std::string(data, size);
	LOG_ERR << str;
}

bool Utility::isDirExist(std::string path)
{
	if (path.length())
	{
		DIR* dir = opendir(path.c_str());
		if (dir != nullptr)
		{
			closedir(dir);
			return true;
		}
	}
	return false;
}

void Utility::initLogging()
{
	if (!isDirExist("./log"))
	{
		mkdir("./log", 00655);
	}
	auto consoleLayout = new PatternLayout();
	// http://log4cpp.sourceforge.net/api/classlog4cpp_1_1PatternLayout.html#a3
	consoleLayout->setConversionPattern("%d: [%t] %p %c: %m%n");
	auto consoleAppender = new OstreamAppender("console", &std::cout);
	consoleAppender->setLayout(consoleLayout);

	//RollingFileAppender(const std::string&name, const std::string&fileName,
	//	size_tmaxFileSize = 10 * 1024 * 1024, unsigned intmaxBackupIndex = 1,
	//	boolappend = true, mode_t mode = 00644);
	auto rollingFileAppender = new RollingFileAppender(
		"rollingFileAppender",
		"./log/camera_monitor.log",
		20 * 1024 * 1024,
		5,
		true,
		00664);

	auto pLayout = new PatternLayout();
	pLayout->setConversionPattern("%d: [%t] %p %c: %m%n");
	rollingFileAppender->setLayout(pLayout);

	Category & root = Category::getRoot();
	root.addAppender(rollingFileAppender);
	root.addAppender(consoleAppender);

	// Log level
	std::string levelEnv = "DEBUG";
	auto env = getenv("LOG_LEVEL");
	if (env != nullptr) levelEnv = env;
	setLogLevel(levelEnv);

	LOG_INF << "Logging process ID:" << getpid();
}

void Utility::setLogLevel(const std::string & level)
{
	std::map<std::string, Priority::PriorityLevel> levelMap = {
		{ "NOTSET", Priority::NOTSET },
	{ "DEBUG", Priority::DEBUG },
	{ "INFO", Priority::INFO },
	{ "NOTICE", Priority::NOTICE },
	{ "WARN", Priority::WARN },
	{ "ERROR", Priority::ERROR },
	{ "CRIT", Priority::CRIT },
	{ "ALERT", Priority::ALERT },
	{ "FATAL", Priority::FATAL },
	{ "EMERG", Priority::EMERG } };

	if (level.length()> 0 && levelMap.find(level) != levelMap.end())
	{
		LOG_INF << "Setting log level to " << level;
		Category::getRoot().setPriority(levelMap[level]);
	}
}

std::chrono::system_clock::time_point Utility::convertStr2Time(const std::string & strTime)
{
	struct tm tm = { 0 };
	tm.tm_isdst = -1;
	std::istringstream ss(strTime);
	// ss.imbue(std::locale("de_DE.utf-8"));
	ss >> std::get_time(&tm, "%Y-%m-%d %H:%M:%S");
	if (ss.fail())
	{
		string msg = "error when convert string to time :";
		msg += strTime;
		throw std::invalid_argument(msg);
	}
	return std::chrono::system_clock::from_time_t(std::mktime(&tm));
}

std::string Utility::convertTime2Str(const std::chrono::system_clock::time_point & time)
{
	// https://en.cppreference.com/w/cpp/io/manip/put_time
	auto timet = std::chrono::system_clock::to_time_t(time);
	std::tm tm = *std::localtime(&timet);
	std::stringstream ss;
	ss << std::put_time(&tm, "%Y-%m-%d %H:%M:%S");
	return ss.str();
}

std::chrono::system_clock::time_point Utility::convertStr2DayTime(const std::string & strTime)
{
	struct tm tm = { 0 };
	tm.tm_isdst = -1;
	// Give a fixed date.
	tm.tm_year = 2000 - 1900;
	tm.tm_mon = 1;
	tm.tm_mday = 17;
	std::istringstream ss(strTime);
	// ss.imbue(std::locale("de_DE.utf-8"));
	ss >> std::get_time(&tm, "%H:%M:%S");
	if (ss.fail())
	{
		string msg = "error when convert string to time :";
		msg += strTime;
		throw std::invalid_argument(msg);
	}
	return std::chrono::system_clock::from_time_t(std::mktime(&tm));
}

std::string Utility::convertDayTime2Str(const std::chrono::system_clock::time_point & time)
{
	// https://en.cppreference.com/w/cpp/io/manip/put_time
	auto timet = std::chrono::system_clock::to_time_t(time);
	std::tm tm = *std::localtime(&timet);
	std::stringstream ss;
	ss << std::put_time(&tm, "%H:%M:%S");
	return ss.str();
}

void Utility::splitString(const std::string & source, std::vector<std::string>& result, const std::string & splitFlag)
{
	std::string::size_type pos1, pos2;
	pos2 = source.find(splitFlag);
	pos1 = 0;
	while (std::string::npos != pos2)
	{
		string str = stdStringTrim(source.substr(pos1, pos2 - pos1));
		if (str.length() > 0) result.push_back(str);

		pos1 = pos2 + splitFlag.size();
		pos2 = source.find(splitFlag, pos1);
	}
	if (pos1 != source.length())
	{
		string str = stdStringTrim(source.substr(pos1));
		if (str.length() > 0) result.push_back(str);
	}
}


bool Utility::getUid(std::string userName, long& uid, long& groupid)
{
	bool rt = false;
	struct passwd pwd;
	struct passwd *result = NULL;
	static auto bufsize = sysconf(_SC_GETPW_R_SIZE_MAX);
	if (bufsize == -1) bufsize = 16384;
	std::shared_ptr<char> buff(new char[bufsize], std::default_delete<char[]>());
	getpwnam_r(userName.c_str(), &pwd, buff.get(), bufsize, &result);
	if (result)
	{
		uid = pwd.pw_uid;
		groupid = pwd.pw_gid;
		rt = true;
	}
	else
	{
		LOG_ERR << "User does not exist: <" << userName << ">.";
	}
	return rt;
}

void Utility::getEnvironmentSize(const std::map<std::string, std::string>& envMap, int & totalEnvSize, int & totalEnvArgs)
{
	// get env size
	if (!envMap.empty())
	{
		auto it = envMap.begin();
		while (it != envMap.end())
		{
			totalEnvSize += (int)(it->first.length() + it->second.length() + 2); // add for = and terminator
			totalEnvArgs++;
			it++;
		}
	}

	// initialize our environment size estimates
	const int numEntriesConst = 256;
	const int bufferSizeConst = 4 * 1024;

	totalEnvArgs += numEntriesConst;
	totalEnvSize += bufferSizeConst;
}

std::string Utility::getSystemPosixTimeZone()
{
	// https://stackoverflow.com/questions/2136970/how-to-get-the-current-time-zone/28259774#28259774
	struct tm local_tm;
	time_t cur_time = 0; // time(NULL);
	localtime_r(&cur_time, &local_tm);

	std::stringstream ss;
	ss << std::put_time(&local_tm, "%Z%z");
	auto str = ss.str();

	// remove un-used zero post-fix :
	// CST+0800  => CST+08
	auto len = str.length();
	for (size_t i = len - 1; i > 0; i--)
	{
		if (str[i] == '0')
		{
			str[i] = '\0';
		}
		else
		{
			str = str.c_str();
			break;
		}
	}
	return str;
}
