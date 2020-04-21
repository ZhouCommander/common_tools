#ifndef __CAPTURE_FFMPEG_H__
#define __CAPTURE_FFMPEG_H__

#include <chrono>
#include <mutex>

#include "capture_template.h"
#include "ace/Process.h"
#include <ace/Thread.h>
#include <ace/Pipe.h>
#include <ace/Event_Handler.h>
#include <ace/Reactor.h>


class CaptureFFMpeg : virtual public CaptureTemplate, virtual public ACE_Event_Handler
{
public:
    CaptureFFMpeg();
    virtual ~CaptureFFMpeg();

    virtual RetCode_E process();

private:
    ACE_Process m_process;

    string m_strPrevFile;
    bool m_bFindNetErr;
    int m_iMissedRTPTotal;
    int m_iMissedRTPSeg;

    time_t m_startCapTime;

	string m_strSeparator;
    string m_strPid;

    int m_reactorId;
    int m_TimerDelay;
    int m_TimerThreshold;
    std::chrono::system_clock::time_point m_lastTime;
    std::recursive_mutex m_mutex;

    RetCode_E parseLine(char *pszLine);
	RetCode_E sendPicMsg();
    RetCode_E stop();
	RetCode_E rename_video_file(string &strFile);
    void rmLastFile();
    void stringReplace(std::string & strBase, const std::string strSrc, const std::string strDst);

 	// wz added 2019-04-28 16:01:17
	void ticker();	
};

#endif

