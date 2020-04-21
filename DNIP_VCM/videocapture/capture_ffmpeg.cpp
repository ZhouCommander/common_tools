
#include <time.h>
#include <chrono>
#include <cstdlib>
#include <thread>

#include <ace/Time_Value.h>
#include <boost/filesystem.hpp>
#include "capture_ffmpeg.h"

#define TAG "<CaptureFFMpeg>"

namespace fs = boost::filesystem;

static const char FFMPEG_DIR[] = "/etc/ffmpeg/";

static const char FFMPEG_QUIT[] = "idummy demux: command `quit'";
static const char FFMPEG_CONN_TIMEOUT[] = "Connection timed out";
static const char FFMPEG_NO_ROUTE[] = "No route to host";
static const char FFMPEG_FILE_OPENING[] = "Opening '";
static const char FFMPEG_FILE_WRITING[] = "' for writing";
static const char FFMPEG_RTP_MISSED[] = "RTP: missed ";
static const char FFMPEG_RTP_PACKETS[] = " packets";
static const char FFMPEG_CONN_REFUSED[] = "Connection refused";
static const char FFMPEG_PIC_END[] = "global headers:";
static const char FFMPEG_PROTOCOL_ERR[] = "Protocol not found";
static const char FFMPEG_DIR_ERR[] = "No such file or directory";
static const char FFMPEG_DISK_QUOTA_EXCEEDED[] = "Disk quota exceeded";
static const char FFMPEG_INTERNAL_SERVER_ERROR[] = "500 Internal Server Error";
static const char FFMPEG_NO_SPACE_LEFT_ON_DEVICE[] = "No space left on device";
static const char FFMPEG_UNKNOWN_ERR[] = "error";



static const int WAIT_MS = 50;
static const int MAX_LINE_LEN = 2048;


CaptureFFMpeg::CaptureFFMpeg()
    :m_strPrevFile(""), m_bFindNetErr(false), m_iMissedRTPTotal(0), m_iMissedRTPSeg(0),
     m_startCapTime(0), m_strSeparator("_"), m_reactorId(-1), m_TimerDelay(60), m_TimerThreshold(0)
{
    m_strPid = std::to_string(getpid());
    m_lastTime = std::chrono::system_clock::now();
}

CaptureFFMpeg::~CaptureFFMpeg()
{
    stop();
}

RetCode_E CaptureFFMpeg::process()
{
    const static char fnName[] = "CaptureFFMpeg::process()";
    LOG_INF << fnName;

    string strFFMpeg = getBaseDir() + string(FFMPEG_DIR) + "ffmpeg";
    if(access(strFFMpeg.c_str(), F_OK) < 0)
    {
        LOG_ERR << " not find 'ffmpeg' in system, please reinstall";
        return RET_ERR_INTERNAL;
    }

    string strCmd = strFFMpeg;
    if(m_param.bRTSPOverTCP)
    {
        strCmd += " -rtsp_transport tcp";
    }
    strCmd += " -hide_banner";
    strCmd += " -i \"" + m_param.strUri + "\"";

    if(m_param.capType == CAP_TYPE_PIC)
    {
        strCmd += " -y";
        //strCmd += " -frames:v 1 ";

		double frameCount = 1.0 / m_param.capTimes_s;
		string strFrameCount = to_string(frameCount);
		strCmd += " -r " + strFrameCount;
		strCmd += " -t " + to_string(m_param.capExitTime_s) + " ";
        strCmd += " -q:v 2 ";
		string dateTime = getCurDayTimeStr(1,'-','-','-');
		//" -strftime 1 " +
        strCmd +=  m_strFilePath + to_string(m_param.cameraID) + "_" + dateTime + m_strSeparator + "%%06d" + ".jpg";
    }
    else if(int(m_param.capTimes_s) == m_param.capExitTime_s)
    {
		int capTimes = static_cast<double>(m_param.capTimes_s);
        strCmd += " -c:v copy -an";
        if(!m_param.strBufSize.empty() && m_param.strBufSize.compare("0") != 0 && m_param.strBufSize.compare("0k") != 0)
        {
            strCmd += string(" -bufsize ") + m_param.strBufSize;
        }
        strCmd += " -t " + to_string(capTimes);
        strCmd += " -strftime 1 " + m_strFilePath + to_string(m_param.cameraID) + "_%%Y-%%m-%%d-%%H-%%M-%%S" + m_strSeparator + to_string(capTimes) + m_strSeparator + m_strPid + ".mp4";
    }
    else
    {
		int capTimes = static_cast<double>(m_param.capTimes_s);
        strCmd += " -c:v copy -an";
        if(!m_param.strBufSize.empty() && m_param.strBufSize.compare("0") != 0 && m_param.strBufSize.compare("0k") != 0)
        {
            strCmd += string(" -bufsize ") + m_param.strBufSize;
        }
        strCmd += " -timeout 5";        // maximum timeout (in seconds) to wait for incoming connections
        strCmd += " -f segment";
        strCmd += " -segment_format mp4";
        if(m_param.bSegAtClockTime)
        {
            strCmd += " -segment_atclocktime 1";
        }
        strCmd += " -segment_time " + std::to_string(capTimes);
        strCmd += " -strftime 1 " + m_strFilePath + to_string(m_param.cameraID) + "_%%Y-%%m-%%d-%%H-%%M-%%S" + m_strSeparator + to_string(capTimes) + m_strSeparator + m_strPid + ".mp4";
    }

    ACE_HANDLE aceHandles[2];
    ACE_Pipe pipeACE;
    int pipeRlt = pipeACE.open(aceHandles);
    if(pipeRlt < 0)
    {
        LOG_ERR << " create pipe failed!";
    }

    ACE_Process_Options option;
	option.command_line(strCmd.c_str());
    if(pipeRlt == 0)
    {
        option.set_handles(ACE_INVALID_HANDLE, pipeACE.write_handle(), pipeACE.write_handle());
    }

    RetCode_E eRet = RET_SUCCESS;
	if (m_process.spawn(option) >= 0)
	{
		m_pid = m_process.getpid();
		LOG_INF << " Process <"<< strCmd <<">, started with pid <"<< m_pid <<">.";

        unsigned int pos = 0;
        char szLine[MAX_LINE_LEN] = {0};

        sendPicMsg();

		m_TimerThreshold = int(m_param.capTimes_s * 1.5);
		if (m_TimerThreshold < 30) m_TimerThreshold = 30;

		// will terminate when ~thread
		std::thread(&CaptureFFMpeg::ticker, this).detach();

        while(eRet == RET_SUCCESS)
        {
            if(pos < MAX_LINE_LEN)
            {
                {
                    std::lock_guard<std::recursive_mutex> guard(m_mutex);
                    m_lastTime = std::chrono::system_clock::now();
                }
                if(ACE_OS::read(pipeACE.read_handle(), szLine+pos, 1) <= 0)
                {
                    {
                        std::lock_guard<std::recursive_mutex> guard(m_mutex);
                        m_lastTime = std::chrono::system_clock::now();
                    }
                    LOG_ERR << " find read error: <"<< strerror(errno) << ">, quit";
                    break;
                }
                {
                    std::lock_guard<std::recursive_mutex> guard(m_mutex);
                    m_lastTime = std::chrono::system_clock::now();
                }
                // line end
                if(szLine[pos] != '\r' && szLine[pos] != '\n')
                {
                    ++pos;
                    continue;
                }
            }
            else
            {
                LOG_ERR << " find length of read line over max len <" << MAX_LINE_LEN << ">, maybe error\r\n";
            }

            // '\r' or '\n' at line start
            if(pos == 0 && (szLine[pos] == '\r' || szLine[pos] == '\n'))
            {
                continue;
            }

            szLine[pos] = END_NULL;

            eRet = parseLine(szLine);
            pos = 0;
            memset(szLine, 0, sizeof(szLine));

			sendPicMsg();
        }

        stop();
	}
	else
	{
		//LOG_ERR << " Process:<%s> start failed with error: %s", strCmd.c_str(), strerror(errno));
		int err = ACE_OS::last_error();
		LOG_ERR << " Process <" << strCmd << "> start failed with error: <" << err << ">";
        if(err)
        {
            eRet = RET_ERR_INTERNAL;
        }
	}

    LOG_INF << " process end, total missed packets: <"<< m_iMissedRTPTotal <<">, return: <" << eRet <<">";
    return eRet;
}

RetCode_E CaptureFFMpeg::sendPicMsg()
{
	RetCode_E eRet = RET_SUCCESS;
	if (m_param.capType == CAP_TYPE_PIC)
	{
		fs::path picPath(m_strFilePath);
		fs::directory_iterator end;
		for (fs::directory_iterator iter(picPath); iter != end; iter++)
		{
			fs::path p = *iter;
			std::string picName = p.leaf().string();
			try
			{
				if (p.extension() == ".jpg")
				{
					time_t lastWriteTime = last_write_time(p);
					time_t currentTime;
					time(&currentTime);
					std::vector<std::string> vectorFileName;
					splitString(picName, vectorFileName, "_");
					string strPicNewName = picName;
					size_t len = vectorFileName.size();
					if (len > 2)
					{
						strPicNewName.clear();
						for (size_t i = 0; i < len; i++)
						{
							if (i == 1)
							{
								string timePic = convertTime2Str(std::chrono::system_clock::from_time_t(lastWriteTime), "%Y-%m-%d-%H-%M-%S");
								strPicNewName.append(timePic);
							}
							else
							{
								strPicNewName.append(vectorFileName[i]);
							}
							if (i != len - 1)
							{
								strPicNewName.append("_");
							}
						}
					}
					double diffTime = difftime(currentTime, lastWriteTime);
					if (diffTime > 4)
					{
						string picNewFullPath = p.parent_path().parent_path().string() + "/" + strPicNewName;
						fs::rename(p, picNewFullPath);
						sendMQ(picNewFullPath, currentTime - lastWriteTime);
					}
				}
			}
			catch (std::exception& e)
			{
				LOG_ERR << " sendPicMsg to MQ exception: <" << e.what() <<">";
			}
		}
	}
	return eRet;
}
RetCode_E CaptureFFMpeg::parseLine(char *pszLine)
{
    RetCode_E eRet = RET_SUCCESS;

    if(strstr(pszLine, "fps=") == NULL)
        LOG_INF << " parse line: <" << pszLine << ">";

    if(strstr(pszLine, FFMPEG_FILE_OPENING) != NULL && strstr(pszLine, FFMPEG_FILE_WRITING) != NULL)
    {
        time_t curTime = time(NULL);
        if(!m_strPrevFile.empty())
        {
			rename_video_file(m_strPrevFile);
            LOG_INF << " saved: <" << m_strPrevFile << ">, missed RTP pkts: <" << m_iMissedRTPSeg << ">";
            sendMQ(m_strPrevFile, curTime-m_startCapTime);
            ++m_iCurSeg;
        }
        m_startCapTime = time(NULL);
        char *pStart = strstr(pszLine, FFMPEG_FILE_OPENING) + sizeof(FFMPEG_FILE_OPENING) - 1;
        char *pEnd = strstr(pszLine, FFMPEG_FILE_WRITING);
        *pEnd = END_NULL;
        m_strPrevFile = pStart;
        m_iMissedRTPSeg = 0;
        m_bFindNetErr = false;
		LOG_INF << " m_iCapSegments:<" << m_iCapSegments << ">, m_iCurSeg: <" << m_iCurSeg << ">.";
        if(m_iCapSegments > 0 && m_iCurSeg >= m_iCapSegments)
        {
            rmLastFile();
            eRet = RET_STOPED;
        }
    }
    else if(strstr(pszLine, FFMPEG_CONN_TIMEOUT) != NULL || strstr(pszLine, FFMPEG_NO_ROUTE) != NULL)
    {
        LOG_INF << " parse line, find net error";
        eRet = RET_ERR_CAMERA_UNAVAILABLE;
    }
	else if (strstr(pszLine, FFMPEG_DISK_QUOTA_EXCEEDED) != NULL)
	{
		LOG_ERR << "error: <" << FFMPEG_DISK_QUOTA_EXCEEDED << ">.";
		eRet = RET_ERR_DISK_QUOTA_EXCEEDED;
	}
	else if (strstr(pszLine, FFMPEG_INTERNAL_SERVER_ERROR) != NULL)
	{
		LOG_ERR << "error: <" << FFMPEG_INTERNAL_SERVER_ERROR << ">.";
		eRet = RET_ERR_INTERNAL_SERVER_ERROR;
	}
	else if (strstr(pszLine, FFMPEG_NO_SPACE_LEFT_ON_DEVICE) != NULL)
	{
		LOG_ERR << "error: <" << FFMPEG_NO_SPACE_LEFT_ON_DEVICE << ">.";
		eRet = RET_ERR_NO_SPACE_LEFT_ON_DEVICE;
	}
    else if(strstr(pszLine, FFMPEG_QUIT) != NULL)
    {
        LOG_INF << " parse line, find quit";
        eRet = RET_STOPED;
		rename_video_file(m_strPrevFile);
        sendMQ(m_strPrevFile, time(NULL)-m_startCapTime);
    }
    else if(strstr(pszLine, FFMPEG_CONN_REFUSED) != NULL)
    {
        LOG_INF << " parse line, find connection refused";
        eRet = RET_ERR_CONN_REFUSED;
    }
    else if(strstr(pszLine, FFMPEG_RTP_MISSED) != NULL && strstr(pszLine, FFMPEG_RTP_PACKETS) != NULL)
    {
        char *pStart = strstr(pszLine, FFMPEG_RTP_MISSED) + sizeof(FFMPEG_RTP_MISSED);
        char *pEnd = strstr(pszLine, FFMPEG_RTP_PACKETS);
        *pEnd = END_NULL;
        int missed = atoi(pStart);
        m_iMissedRTPSeg += missed;
        m_iMissedRTPTotal += missed;
        LOG_INF << " find RTP missed packets: <" << m_iMissedRTPTotal << ">";
    }
    else if(strstr(pszLine, FFMPEG_PIC_END) != NULL)
    {
        if(m_param.capType == CAP_TYPE_PIC)
        {
            LOG_INF << " find capture pic end";
            eRet = RET_STOPED;
        }
    }
    else if(strstr(pszLine, FFMPEG_PROTOCOL_ERR) != NULL)
    {
        LOG_INF << " parse line, find protocol error in url";
        eRet = RET_ERR_CAMERA_UNAVAILABLE;
    }
    else if(strstr(pszLine, FFMPEG_DIR_ERR) != NULL)
    {
        if(strstr(pszLine, m_param.strUri.c_str()) != NULL)
        {
            LOG_INF << " parse line, find url error";
            eRet = RET_ERR_CAMERA_UNAVAILABLE;
        }
        else
        {
            LOG_INF << " parse line, find dir or file error, maybe no permisson?";
            eRet = RET_ERR_NO_PERMISSION_WRITE;
        }
    }
    else
    {
		//avoid  zombie process
        // try to wait ,if wait sucess return RET_STOPED
		ACE_Time_Value tv;
		tv.msec(WAIT_MS);
		//wait sucess
		if (m_process.wait(tv) > 0)
		{
            LOG_INF << " ffmpeg already exit, pszLine <" << pszLine << ">.";
            auto ret = m_process.return_value();
            if (ret != 0)
            {
                LOG_WAR << "ffmpeg returns : <" << ret << ">.";
                eRet = RET_STOPED;
            }
            else
            {
                eRet = RET_STOPED;
            }
        }
    }
    return eRet;
}

RetCode_E CaptureFFMpeg::stop()
{
	std::lock_guard<std::recursive_mutex> guard(m_mutex);
    if(m_process.running())
    {
        m_process.terminate();

        //avoid  zombie process
        //ACE_Time_Value tv;
       // tv.msec(WAIT_MS);
        m_process.wait();

        LOG_INF << " Process <" << m_pid << "> stopped";
    }
    return RET_SUCCESS;
}

void CaptureFFMpeg::rmLastFile()
{
    ACE_OS::unlink(m_strPrevFile.c_str());
    LOG_INF << " remove last file: <" << m_strPrevFile << ">.";
}


RetCode_E CaptureFFMpeg::rename_video_file(string &strFile)
{
	RetCode_E eRet = RET_SUCCESS;
	// delete pid from strFile
    string newStrFile = strFile;
	string suffix = m_strSeparator + m_strPid + ".";
    stringReplace(newStrFile, suffix, ".");
    if(strFile != newStrFile)
    {
        try
        {
            ACE_OS::rename(strFile.c_str(), newStrFile.c_str());
            strFile = newStrFile;
            LOG_INF << " rename video file success, src: " << strFile << ", dst: " << newStrFile;
        }
        catch (...)
        {
            LOG_ERR << " rename video file failed, src: " << strFile << ", dst: " << newStrFile;
            eRet = RET_ERR_INTERNAL;
        }
    }
    else
    {
        LOG_WAR << "video file not renamed : " << strFile ;
    }

	return eRet;
}

void CaptureFFMpeg::stringReplace(std::string & strBase, const std::string strSrc, const std::string strDst)
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

void CaptureFFMpeg::ticker()
{
	LOG_INF << "CaptureFFMpeg::startTicker() ";
	// time delay 60s
	std::this_thread::sleep_for(std::chrono::seconds(m_TimerDelay));
	// will not exit.
	std::chrono::seconds gap(0);
	while (true)
	{
		{
			std::lock_guard<std::recursive_mutex> guard(m_mutex);
			gap = std::chrono::duration_cast<std::chrono::seconds>(std::chrono::system_clock::now() - m_lastTime);
		}
		if (gap > std::chrono::seconds(m_TimerThreshold))
		{
			stop();
			LOG_ERR << "Find timeout, exit(2)";
			_exit(2);
		}
		std::this_thread::sleep_for(std::chrono::seconds(int(m_param.capTimes_s / 2)));
	}
}
