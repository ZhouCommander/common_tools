#ifndef __CAPTURE_COMMON_H__
#define __CAPTURE_COMMON_H__

#include <stdio.h>
#include <stdlib.h>
#include <stddef.h>
#include <string.h>
#include <string>
#include <errno.h>

#include <ace/Log_Msg.h>

using std::string;
using std::to_string;

#include <log4cpp/Category.hh>
#include <log4cpp/Appender.hh>
#include <log4cpp/FileAppender.hh>
#include <log4cpp/Priority.hh>
#include <log4cpp/PatternLayout.hh>
#include <log4cpp/RollingFileAppender.hh>

using namespace log4cpp;

#define __FILENAME__ (strrchr(__FILE__, '/') ? strrchr(__FILE__, '/') + 1 : __FILE__)
#define LOG_TRC    log4cpp::Category::getRoot() << log4cpp::Priority::TRACE << __FILENAME__ << ":" << __LINE__ << ' '
#define LOG_DBG    log4cpp::Category::getRoot() << log4cpp::Priority::DEBUG << __FILENAME__ << ":" << __LINE__ << ' '
#define LOG_INF    log4cpp::Category::getRoot() << log4cpp::Priority::INFO << __FILENAME__ << ":" << __LINE__ << ' '
#define LOG_WAR    log4cpp::Category::getRoot() << log4cpp::Priority::WARN << __FILENAME__ << ":" << __LINE__ << ' '
#define LOG_ERR    log4cpp::Category::getRoot() << log4cpp::Priority::ERROR << __FILENAME__ << ":" << __LINE__ << ' '




#define SEPARATOR   '/'
#define END_NULL    '\0'

#define DIR_MODE    0777


typedef enum VideoEncodecTag
{
    V_CODEC_H264,
    V_CODEC_MP4V,
} VideoEncodec_E;

typedef enum AudioEncodecTag
{
    A_CODEC_MPGA,
    A_CODEC_MP3,
} AudioEncodec_E;

typedef enum CaptureMuxTag
{
    MUX_MP4,
    MUX_AVI,
    MUX_ASF,
    MUX_OGG,
    MUX_TS,
} CaptureMux_E;

typedef enum CaptureAccessTag
{
    ACCESS_FILE,
    ACCESS_RTSP,
} CaptureAccess_E;

typedef enum CaptureTypeTag
{
    CAP_TYPE_VIDEO,
    CAP_TYPE_PIC,
} CaptureType_E;

typedef enum CaptureInterfaceTag
{
    CAP_VLC,
    CAP_VLC_LIB,
    CAP_FFMPEG,
    CAP_FFMPEG_LIB,
} CaptureInterface_E;

typedef enum CaptureStatusTag
{
    CAP_STATUS_UNKNOWN,
    CAP_STATUS_RUNNING,
    CAP_STATUS_STOP,
    CAP_STATUS_ERR,
} CaptureStatus_E;

typedef enum RetCodeTag
{
    RET_SUCCESS = 0,
    RET_STOPED = -1,

	RET_UNKOWN_ERROR = 50,
    RET_ERR_CAMERA_UNAVAILABLE = 51,
    RET_ERR_NO_ENOUGH_DISK = 52,
    RET_ERR_NO_PERMISSION_WRITE = 53,
    RET_ERR_CONN_REFUSED = 54,
	RET_ERR_DISK_QUOTA_EXCEEDED = 55,
	RET_ERR_INTERNAL_SERVER_ERROR = 56,
	RET_ERR_NO_SPACE_LEFT_ON_DEVICE  = 57,

    RET_ERR_PARAM = 100,
    RET_ERR_INTERNAL = 101,
} RetCode_E;


typedef struct CaptureParamTag
{
    string strUri;                      // camera stream url
    int cameraID;                       // camera id
    string strMsgQueueUri;              // MQ url
    string strMsgQueueName;             // MQ name
    CaptureType_E capType;              // capture type, default CAP_TYPE_VIDEO
    double capTimes_s;                     // capture duration of one segment, seconds, default 5min
    int capExitTime_s;                  // capture total times, seconds, default 0, mean not control
    string strBaseDir;                  // the base dir will to be save video file, default /opt/deepnorth
    bool bSegAtClockTime;               // switch segment at clock time when true, default true
    bool bRTSPOverTCP;                  // transport rtp over tcp when true, otherwise udp, default false
    string strBufSize;                  // ffmpeg param bufsize

    CaptureMux_E recMux;                // output muxe
    CaptureAccess_E recAccess;          // output protocol

    int vWidth;                         // the width of video
    int vHeight;                        // the height of video
    int vBps;                           // the bitrates of video, bps
    int vFps;                           // the framerates of video
    VideoEncodec_E vEnc;                // encode type of video

    int aSampleRate;                    // the sample rate of audio
    int aBps;                           // the bitrates of audio, bps
    AudioEncodec_E aEnc;                // encode type of audio

    // wz added
    string jsonPath;                    // where to put json

    // use for main
    CaptureInterface_E capInterface;    // module of capture used, default CAP_FFMPEG

    CaptureParamTag()
        :strUri(""), cameraID(0), strMsgQueueUri(""), strMsgQueueName(""), capType(CAP_TYPE_VIDEO),
        capTimes_s(5*60), capExitTime_s(0), strBaseDir("/opt/deepnorth"),
        bSegAtClockTime(true), bRTSPOverTCP(false),strBufSize("4096k"),
        recMux(MUX_MP4), recAccess(ACCESS_FILE),
        vWidth(0), vHeight(0), vBps(0), vFps(0), vEnc(V_CODEC_MP4V),
        aSampleRate(0), aBps(0), aEnc(A_CODEC_MPGA), capInterface(CAP_FFMPEG)
    {
    }
} CaptureParam_ST;


void mkdirs(string &strDir, int mode);
string getBaseDir();

std::chrono::system_clock::time_point convertStr2Time(const string & strTime, const string & strFormat);
string convertTime2Str(const std::chrono::system_clock::time_point & time, const string & strFormat);

// type: 1--all, 2--only day, 3--only time, default 1
string getCurDayTimeStr(int type=1, char sepDay='-', char sepJoin='_', char sepTime='.');
string getDayTimeFromString(string &strFile);
void splitString(const string & source, std::vector<string>& result, const string & splitFlag);
string stdStringTrim(const string & str);

// wz added 
void initLogging(int cameraid);
void setLogLevel(const std::string & level);

#endif

