#ifndef __CAPTURE_TEMPLATE_H__
#define __CAPTURE_TEMPLATE_H__

#include "capture_common.h"
#include "capture_sendmq.h"


class CaptureTemplate
{    
public:    
    CaptureTemplate();
    virtual ~CaptureTemplate();

    RetCode_E run(CaptureParam_ST &param);

public:
    CaptureParam_ST m_param;
    int m_pid;

    string m_strFilePath;
    int m_iCapSegments;
    int m_iCurSeg;

    virtual RetCode_E process() = 0;

    void sendMQ(string &strFile, time_t capDur);
    string getFileName();

    // wz added 2019-03-05 18:39:43 call after sendMQ()
    void saveJson(std::string &strFile);
private:
    CaptureSendMQ m_cSendMQ;
};

#endif

