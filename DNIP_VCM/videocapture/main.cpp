#include <stddef.h>
#include <unistd.h>
#include <string.h>
#include <getopt.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <fstream>
#include <iostream>
#include <thread>
#include <ace/Init_ACE.h>
#include <ace/Reactor.h>
// #include <ace/Log_Msg.h>

//#include "../common/utility.h"
#include "capture_common.h"
#include "capture_template.h"
#include "capture_vlc.h"
#include "capture_ffmpeg.h"

#define CAPTURE_TYPE_VIDEO  "video"
#define CAPTURE_TYPE_PIC  "pic"
#define CAPTURE_INTERFACE_VLC "vlc"
#define CAPTURE_INTERFACE_VLC_LIB "vlc_lib"
#define CAPTURE_INTERFACE_FFMPEG "ffmpeg"
#define CAPTURE_INTERFACE_FFMPEG_LIB "ffmpeg_lib"

#define LOG_DIR "log"
#define LOG_FILENAME "videocapture"

#define TAG "<MAIN>"

#define __MICRO_KEY__(str) #str					// No expand micro
#define __MICRO_VAR__(str) __MICRO_KEY__(str)	// Expand micro
 #define PRINT_VERSION() if (argc >= 2 && (std::string("version") == argv[1] || std::string("-v") == argv[1] || std::string("-V") == argv[1])) \
 	    { std::cout << "Build: " << __MICRO_VAR__(BUILD_TAG) << std::endl; 	return 0; }

static const size_t MAX_INT_LEN = 12;
static const int MAX_CAP_INTERVAL = 3600;

static ofstream logStream;

static void usage(char *argv[])
{
    printf("usage:\r\n");
    printf("      %s -c URL -u CAMERA_ID [-t CAPTURE_TYPE] [-q MSG_QUEUE -n MSG_QUEUE_NAME] [-i INTERVAL_SEC] [-e EXIT_TIME_SEC] [-d MEDIA_STORE_DIR] [-p CAPTURE_INTERFACE] [-a VALUE] [-b VALUE] [-r VALUE]\r\n", argv[0]);
    printf("      option:\r\n");
    printf("          -c URL                 camera rtsp address\r\n");
    printf("          -u CAMERA_ID           camera id\r\n");
    printf("          -t CAPTURE_TYPE        capture type: video/pic, default video\r\n");
    printf("          -q MSG_QUEUE           message queue address, default empty\r\n");
    printf("          -n MSG_QUEUE_NAME      message queue name, default empty\r\n");
    printf("          -i INTERVAL_SEC        interval seconds, default 5min\r\n");
    printf("          -e EXIT_TIME_SEC       exit cap seconds, default 0\r\n");
    printf("          -d MEDIA_STORE_DIR     media store directory, default is /opt/deepnorth/ \r\n");
    printf("          -p CAPTURE_INTERFACE   capture interface: vlc/vlc_lib/ffmpeg/ffmpeg_lib, default ffmpeg\r\n");
    printf("          -a VALUE               switch segment at clock time, 0 is off, 1 is on, default 1\r\n");
    printf("          -b VALUE               ffmpeg param bufsize, 0 or 0k means not set, default 4096k\r\n");
    printf("          -r VALUE               transport rtp use udp or tcp, default udp\r\n");
    // wz added 
    printf("          -j PATHs               where to save the json file\r\n");
}

static RetCode_E getOpt(int argc, char *argv[], CaptureParam_ST &param)
{
    size_t len = 0;
    int opt=0;
	if (1 == argc)
	{
		usage(argv);
		return RET_STOPED;
	}

    while((opt=getopt(argc,argv,"c:u:t:q:n:i:d:p:e:a:b:r:j:k:h")) != -1)
    {
        switch(opt)
        {
            case 'c':
                len = strlen(optarg);
                if(len <= 0)
                {
                    // LOG_ERR << " getOpt <" << opt << "> len <" << len << ">";
                    return RET_ERR_PARAM;
                }
                param.strUri = optarg;
                // LOG_INF << " getOpt find srcUri:<" << len << ">, uri <" << param.strUri << ">.";
                break;
            case 'u':
                len = strlen(optarg);
                if(len <= 0 || MAX_INT_LEN <= len)
                {
                    // LOG_ERR << " getOpt <" << opt << "> len <" << len << ">";
                    return RET_ERR_PARAM;
                }
                param.cameraID = atoi(optarg);
                // LOG_INF << " getOpt find camera id <" << param.cameraID << ">.";
                break;
            case 't':
                if(strcasecmp(optarg, CAPTURE_TYPE_VIDEO) == 0)
                {
                    param.capType = CAP_TYPE_VIDEO;
                }
                else if(strcasecmp(optarg, CAPTURE_TYPE_PIC) == 0)
                {
                    param.capType = CAP_TYPE_PIC;
                }
                else
                {
                    // LOG_ERR << " getOpt <" << opt << ">, optaarg <" << optarg << ">.";
                    return RET_ERR_PARAM;
                }
                // LOG_INF << " getOpt find capture type: <" << param.capType << ">.";
                break;
            case 'q':
                len = strlen(optarg);
                if(len <= 0)
                {
                    // LOG_ERR << " getOpt <" << opt << ">, len <" << len << ">.";
                    return RET_ERR_PARAM;
                }
                param.strMsgQueueUri = optarg;
                // LOG_INF << " getOpt find msgQueueUri <" << param.strMsgQueueUri << ">.";
                break;
            case 'n':
                len = strlen(optarg);
                if(len <= 0)
                {
                    // LOG_ERR << " getOpt <" << opt << ">, len <" << len << ">.";
                    return RET_ERR_PARAM;
                }
                param.strMsgQueueName = optarg;
                // LOG_INF << " getOpt find msgQueueName: <" << param.strMsgQueueName << ">.";
                break;
            case 'i':
                len = strlen(optarg);
                if(len <= 0 || MAX_INT_LEN <= len)
                {
                    // LOG_ERR << " getOpt <" << opt << ">, len <" << len << ">.";
                    return RET_ERR_PARAM;
                }
                param.capTimes_s = atof(optarg);
                // LOG_INF << " getOpt find rec times: <" << param.capTimes_s << ">.";
                break;
            case 'd':
                len = strlen(optarg);
                if(len <= 0)
                {
                    // LOG_ERR << " getOpt <" << opt << ">, len <" << len << ">";
                    return RET_ERR_PARAM;
                }
                param.strBaseDir = optarg;
                if(optarg[len-1] == '/')
                {
                    param.strBaseDir = param.strBaseDir.substr(0, len-1);
                }
                // LOG_INF << " getOpt find base dir:<" << param.strBaseDir << ">";
                break;
            case 'p':
                if(strcasecmp(optarg, CAPTURE_INTERFACE_VLC) == 0)
                {
                    param.capInterface = CAP_VLC;
                }
                else if(strcasecmp(optarg, CAPTURE_INTERFACE_VLC_LIB) == 0)
                {
                    param.capInterface = CAP_VLC_LIB;
                }
                else if(strcasecmp(optarg, CAPTURE_INTERFACE_FFMPEG) == 0)
                {
                    param.capInterface = CAP_FFMPEG;
                }
                else if(strcasecmp(optarg, CAPTURE_INTERFACE_FFMPEG_LIB) == 0)
                {
                    param.capInterface = CAP_FFMPEG_LIB;
                }
                else
                {
                    // LOG_ERR << " getOpt <" << opt << ">, optaarg <" << optarg << ">.";
                    return RET_ERR_PARAM;
                }
                // LOG_INF << " getOpt find capInterface <" << param.capInterface << ">";
                break;
            case 'e':
                len = strlen(optarg);
                if(len <= 0 || MAX_INT_LEN <= len)
                {
                    // LOG_ERR << " getOpt <" << opt << ">, optaarg <" << optarg << ">.";
                    return RET_ERR_PARAM;
                }
                param.capExitTime_s = atoi(optarg);
                // LOG_INF << " getOpt find exit time: <" << param.capExitTime_s << ">.";
                break;
            case 'a':
                param.bSegAtClockTime = (strcmp(optarg, "1") == 0);
                // LOG_INF << " getOpt find SegAtClockTime <" << optarg << ">.";
                break;
            case 'b':
                param.strBufSize = optarg;
                // LOG_INF << " getOpt find strBufSize <" << optarg << ">.";
                break;
            case 'r':
                param.bRTSPOverTCP = (strcasecmp(optarg, "tcp") == 0);
                // LOG_INF << " getOpt find RTSPOverTCP <" << optarg << ">.";
                break;
            case 'h':
                usage(argv);
                // LOG_ERR << " getOpt <" << opt << ">.";
                return RET_STOPED;
                break;
            case 'j':
                len = strlen(optarg);
                if (len <= 0)
                {
                    // LOG_ERR << " getOpt <" << opt << ">, len <" << len << ">";
                    return RET_ERR_PARAM;
                }
				param.jsonPath = string(optarg) + "/camera_status";
                // LOG_INF << " getOpt find jsonPath: <" << param.jsonPath << ">." ;
                break;
            case 'k':
                len = strlen(optarg);
                if (len <= 0)
                {
                    // LOG_ERR << " getOpt <" << opt << ">, len <" << len << ">";
                    return RET_ERR_PARAM;
                }
                param.strMsgQueueName = "";
                break;
            default:
                break;
        }
    }

    LOG_INF << " getOpt over";
    return RET_SUCCESS;
}

static RetCode_E checkParam(CaptureParam_ST &param)
{
    if(param.cameraID < 0)
    { 
        LOG_ERR << " checkParam find error, cameraID: <" << param.cameraID << ">";
        return RET_ERR_PARAM;
    }

    if(param.capTimes_s <= 0 || MAX_CAP_INTERVAL < param.capTimes_s)
    {
        LOG_ERR << " checkParam find error, recTimes_s: <" << param.capTimes_s << ">";
        return RET_ERR_PARAM;
    }

    if(param.capExitTime_s < 0)
    {
        LOG_ERR << " checkParam find error, capExitTime_s: <" << param.capExitTime_s << ">";
        return RET_ERR_PARAM;
    }

    if(param.capExitTime_s != 0 && param.capTimes_s > param.capExitTime_s)
    {
        LOG_ERR << " checkParam find error, capTimes > exitTime";
        return RET_ERR_PARAM;
    }

    if(param.strMsgQueueUri.empty())
    {
        LOG_ERR << " checkParam find error, MsgQueueUri is empty";
        return RET_ERR_PARAM;
    }

    return RET_SUCCESS;
}

static CaptureTemplate* createCaptureObj(CaptureParam_ST &param)
{
    static const char fnName[] = "static CaptureTemplate* createCaptureObj()  ";
    LOG_INF << fnName;

    CaptureTemplate* pCap = NULL;
    if(param.capInterface == CAP_VLC)
    {
        pCap = new CaptureVLC();
        LOG_INF << " start capture vlc";
    }
    else if(param.capInterface == CAP_VLC_LIB)
    {
    }
    else if(param.capInterface == CAP_FFMPEG)
    {
        pCap = new CaptureFFMpeg();
        LOG_INF << " start capture ffmpeg";
    }
    else if(param.capInterface == CAP_FFMPEG_LIB)
    {
    }
    else
    {
        // error
    }
    return pCap;
}
// 
// void TimerLoopThread()
// {
//     ACE_Reactor::instance()->run_event_loop();
// }

int main(int argc, char *argv[])
{
    const static char fname[] = "main() ";
	  PRINT_VERSION();
    CaptureParam_ST param;

    ACE::init();
    // auto thread = std::make_shared<std::thread>(TimerLoopThread);
    LOG_INF << fname;

    RetCode_E eRet = RET_SUCCESS;
    CaptureTemplate *pCap = NULL;
    try
	{     
        LOG_INF << fname;
        eRet = getOpt(argc, argv, param);
        initLogging(param.cameraID);
        LOG_INF << fname;
        LOG_INF << "camera stream url: strUri<" << param.strUri << ">,"
            << "camera id: cameraID<" << param.cameraID << ">,"
            << "capture type: capType<" << param.capType << ">,"
            << "msgQueueUri: strMsgQueueUri<" << param.strMsgQueueUri << ">,"
            << "msgQueueName: strMsgQueueName<" << param.strMsgQueueName << ">,"
            << "capture duration: capTimes_s<" << param.capTimes_s << ">,"
            << "base directory: strBaseDir<" << param.strBaseDir << ">."
            << "module of capture used: capInterface<" << param.capInterface << ">,"
            << "capture total times: capExitTime_s<" << param.capExitTime_s << ">,"
            << "switch segment at clock time ?<" << param.bSegAtClockTime << ">,"
            << "strBufSize<" << param.strBufSize << ">,"
            << "transport rtp over tcp ? <" << param.bRTSPOverTCP << ">.";

        if(eRet == RET_SUCCESS)
        {
            eRet = checkParam(param);
            if(eRet == RET_SUCCESS)
            {
                // init log again with cameraID
                pCap = createCaptureObj(param);
                if(pCap != NULL)
                {
                    eRet = pCap->run(param);
                }
            }
            else
            {
                LOG_ERR << " param error ";
            }
        }
        else if(eRet == RET_STOPED)
        {
            // no action
        }
        else
        {
            LOG_ERR << " parse param error ";
        }
    }
    catch (const std::exception& e)
    {
        LOG_ERR << " ERROR: <" << e.what() << ">.";
    }
    catch (...)
    {
        LOG_ERR << " ERROR: unknown exception.";
    }

    LOG_INF << " main end <" << eRet << ">.";

    if(pCap != NULL)
    {
        delete pCap;
        pCap = NULL;
    }

    logStream.close();
//     if(thread != NULL)
//     {
//         ACE_Reactor::instance()->end_event_loop();
//         thread->join();
//     }
    ACE::fini();
	if (eRet > 0) _exit(eRet);
	_exit(0);
	return 0;
}

