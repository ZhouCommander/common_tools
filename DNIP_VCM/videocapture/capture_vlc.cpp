#include "capture_vlc.h"
#include <time.h>

#include <ace/Time_Value.h>

#define TAG "<CaptureVLC>"

static const useconds_t SLEEP_US = 50*1000;
static const int WAIT_MS = 50;

static const char VLC_DIR[] = "/etc/vlc/";

static const char VLC_ACCESS_FILE[] = "file";
static const char VLC_ACCESS_RTSP[] = "rtsp";
static const char VLC_MUX_MP4[] = "mp4";

CaptureVLC::CaptureVLC()
{
}

CaptureVLC::~CaptureVLC()
{
    stop();
}

RetCode_E CaptureVLC::process()
{
    const static char fnName[] = "CaptureVLC::process()  ";
    LOG_INF << fnName;

    RetCode_E eRet = RET_SUCCESS;
    time_t timeStartProcess = time(NULL);

    do
    {
        time_t timeStart = time(NULL);

        eRet = createVLCProcess();
        if(eRet != RET_SUCCESS)
        {
            break;
        }

        while(true)
        {
            time_t cur = time(NULL);
            if((cur - timeStart) >= m_param.capTimes_s || (m_param.capExitTime_s > 0 && (cur - timeStartProcess) >= m_param.capExitTime_s))
            {
                //LOG_INF << " find record time end\r\n");
                LOG_INF << " find record time end";
                break;
            }
            usleep(SLEEP_US);
        }

        stop();
        sendMQ(m_strFileName, m_param.capTimes_s);
        ++m_iCurSeg;
    } while (eRet == RET_SUCCESS && (m_iCapSegments <= 0 || (m_iCapSegments > 0 && m_iCurSeg < m_iCapSegments)));

    LOG_INF << " process end, return " << eRet;
    return eRet;
}

RetCode_E CaptureVLC::createVLCProcess()
{
    const static char fnName[] = "CaptureVLC::createVLCProcess()  ";
    LOG_INF << fnName;
    m_strFileName = m_strFilePath + getFileName();

    string strVLC = getBaseDir() + string(VLC_DIR) + "cvlc";
    if(access(strVLC.c_str(), F_OK) < 0)
    {
        LOG_ERR << " not find 'cvlc' in system, please reinstall";        
        return RET_ERR_INTERNAL;
    }

    string strCmd = strVLC + " \"" + m_param.strUri + "\"";
    if(m_param.capType == CAP_TYPE_PIC)
    {
        strCmd += "";                   // fix me ----------------------------------------------
    }
    else
    {
        strCmd += " --sout=#duplicate{dst=std{access=";
        strCmd += (m_param.recAccess != ACCESS_RTSP)?VLC_ACCESS_FILE:VLC_ACCESS_RTSP;
        strCmd += ",mux=";
        strCmd += VLC_MUX_MP4;          // fix me ---------------------------------------------------
        strCmd += ",dst='" + m_strFileName + "'";
        strCmd += "},dst=nodisplay}";
        //strCmd += " :ttl=1 :sout-keep";
        //strCmd += " --run-time=3600";
        strCmd += " vlc://quit";
    }

    ACE_Process_Options option;
	option.command_line(strCmd.c_str());
	if (m_process.spawn(option) < 0)
	{
		m_pid = -1;
		LOG_ERR << " createVLCProcess: <" << strCmd  << ">, start failed with error: <" << strerror(errno) << ">.";
        return RET_ERR_INTERNAL;
	}

    m_pid = m_process.getpid();
	LOG_INF << " createVLCProcess <" << strCmd << ">, started with pid <" << m_pid << ">.";
    return RET_SUCCESS;
}

RetCode_E CaptureVLC::stop()
{
    const static char fnName[] = "CaptureVLC::stop()  ";
    LOG_INF << fnName;
    if(m_process.running())
    {
        m_process.kill();

        //avoid  zombie process
        ACE_Time_Value tv;
        tv.msec(WAIT_MS);
        m_process.wait();

        LOG_INF << " Process <"<< m_pid << "> stopped";
    }
    return RET_SUCCESS;
}

