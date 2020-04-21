#ifndef __CAPTURE_VLC_H__
#define __CAPTURE_VLC_H__

#include "capture_template.h"
#include "ace/Process.h"
#include <ace/Thread.h>


class CaptureVLC : public CaptureTemplate
{
public:
    CaptureVLC();
    virtual ~CaptureVLC();

    virtual RetCode_E process();

private:
    ACE_Process m_process;
    string m_strFileName;

    RetCode_E createVLCProcess();
    RetCode_E stop();
};

#endif

