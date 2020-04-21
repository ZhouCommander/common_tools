#include "capture_common.h"
#include <sys/stat.h>
#include <sstream>
#include <iomanip>
#include <ctime>

#include <log4cpp/OstreamAppender.hh>




void mkdirs(string &strDir, int mode)
{
    umask(0);
    size_t pos = 0;
    while(string::npos != (pos = strDir.find(SEPARATOR, pos)))
    {
        mkdir(strDir.substr(0, pos).c_str(), mode);
        ++pos;
    }
    mkdir(strDir.c_str(), mode);
}

string getBaseDir()
{
    char szDir[PATH_MAX] = {0};
    ssize_t count = readlink("/proc/self/exe", szDir, sizeof(szDir));
    if(0 <= count && count < ((ssize_t)sizeof(szDir)))
    {
        char *pEnd = strrchr(szDir, SEPARATOR);
        *pEnd = END_NULL;
    }
    return szDir;
}

std::chrono::system_clock::time_point convertStr2Time(const string & strTime, const string & strFormat)
{
	struct tm tm = { 0 };
    tm.tm_isdst = -1;
	std::istringstream ss(strTime);
	// ss.imbue(std::locale("de_DE.utf-8"));
	ss >> std::get_time(&tm, strFormat.c_str());
	if (ss.fail())
	{
		return std::chrono::system_clock::from_time_t(0);
	}
	return std::chrono::system_clock::from_time_t(std::mktime(&tm));
}

string convertTime2Str(const std::chrono::system_clock::time_point & time, const string & strFormat)
{
	// https://en.cppreference.com/w/cpp/io/manip/put_time
	auto timet = std::chrono::system_clock::to_time_t(time);
	std::tm tm = *std::localtime(&timet);
	std::stringstream ss;
	ss << std::put_time(&tm, strFormat.c_str());
	return ss.str();
}

// type: 1--all, 2--only day, 3--only time, default 1
string getCurDayTimeStr(int type, char sepDay, char sepJoin, char sepTime)
{
    string strFormat;
    string strDayTimeStr = "";
    std::chrono::system_clock::time_point curTime = std::chrono::system_clock::from_time_t(time(NULL));

    if(type == 1)
    {
        strFormat = string("%Y") + sepDay + string("%m") + sepDay + string("%d") + sepJoin +
                    string("%H") + sepTime + string("%M") + sepTime + string("%S");
        strDayTimeStr = convertTime2Str(curTime, strFormat);
    }
    else if(type == 2)
    {
        strFormat = string("%Y") + sepDay + string("%m") + sepDay + string("%d");
        strDayTimeStr = convertTime2Str(curTime, strFormat);
    }
    else if(type == 3)
    {
        strFormat = string("%H") + sepTime + string("%M") + sepTime + string("%S");
        strDayTimeStr = convertTime2Str(curTime, strFormat);
    }
    else
    {
        // error
    }
    return strDayTimeStr;
}

string getDayTimeFromString(string &strFile)
{
    int locfilename = strFile.find_last_of('/');
	string strFileName = strFile.substr(locfilename + 1, strFile.length() - locfilename - 1);
	std::vector<string> videoFileName;
	splitString(strFileName,videoFileName,"_");
	string strTime;
	if (videoFileName.size() > 2)
	{
		strTime = videoFileName.at(1);
	}
    std::chrono::system_clock::time_point filetime = convertStr2Time(strTime, "%Y-%m-%d-%H-%M-%S");
	return convertTime2Str(filetime, "%Y-%m-%d %H:%M:%S");
}

void splitString(const string & source, std::vector<string>& result, const string & splitFlag)
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


string stdStringTrim(const string & str)
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

void initLogging(int cameraid)
{
    if (access("./log", W_OK))
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
    std::string logFileName = "./log/video_capture_" + std::to_string(cameraid) + ".log";
    auto rollingFileAppender = new RollingFileAppender(
        "rollingFileAppender",
        logFileName,
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

void setLogLevel(const std::string & level)
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

    if (level.length() > 0 && levelMap.find(level) != levelMap.end())
    {
        LOG_INF << "Setting log level to " << level;
        Category::getRoot().setPriority(levelMap[level]);
    }
}

