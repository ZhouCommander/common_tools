#include "capture_template.h"
#include <math.h>
#include <fstream>

#define TAG "<CaptureTemplate>"


CaptureTemplate::CaptureTemplate()
    :m_pid(-1), m_strFilePath(""), m_iCapSegments(0), m_iCurSeg(0)
{
}

CaptureTemplate::~CaptureTemplate()
{
}

RetCode_E CaptureTemplate::run(CaptureParam_ST &param)
{
    const static char fnName[] = "CaptureTemplate::run  ";
    LOG_INF << fnName;

    m_param = param;

    m_strFilePath = m_param.strBaseDir;
    m_strFilePath += "/" + to_string(m_param.cameraID);
    m_strFilePath += "/" + getCurDayTimeStr(2, '-');
	if (m_param.capType == CAP_TYPE_PIC)
	{
		m_strFilePath += "/.cache_pic";
	}
    m_strFilePath += "/";
    mkdirs(m_strFilePath, DIR_MODE);

    // calc segments
    if(m_param.capExitTime_s > 0)
    {
        m_iCapSegments = ceil(m_param.capExitTime_s * 1.0 / m_param.capTimes_s);
        LOG_INF << " capture segments <" << m_iCapSegments << ">. ";
    }

    return this->process();
}

void CaptureTemplate::sendMQ(string &strFile, time_t capDur)
{    
    if(m_param.strMsgQueueUri.empty() || m_param.strMsgQueueName.empty())
    {
        LOG_INF << " sendMQ find url or name is empty, not send";
        return;
    }
    string strMQRoot = "/";
    m_cSendMQ.init(m_param.strMsgQueueUri, strMQRoot, m_param.strMsgQueueName);
    m_cSendMQ.sendMQ(m_param, strFile, capDur);
    LOG_INF << " sendMQ end";
    // wz added save to jsonfile
    saveJson(strFile);
}

string CaptureTemplate::getFileName()
{
    string suffix = "mp4";
    if(m_param.capType == CAP_TYPE_PIC)
    {
        suffix = "jpg";
    }
    
    return to_string(m_param.cameraID) + getCurDayTimeStr(1, '-', '-', '_') + "_" + to_string(m_param.capTimes_s) + "." + suffix;
}


void CaptureTemplate::saveJson(std::string &strFile)
{   
    try 
    {
        const static char fnName[] = "CaptureTemplate::saveJson()  ";
        LOG_INF << fnName << "strFile <" << strFile << ">.";

        if (m_param.jsonPath.empty())
        {
            // no -j do nothing
            LOG_INF << "saveJson directly returns since switch is off.";
            return;
        }


        struct stat filestatus;
        if (stat(m_param.jsonPath.c_str(), &filestatus) == 0 || S_ISDIR(filestatus.st_mode))
        {
            LOG_INF << "save json to <" << m_param.jsonPath << ">.";
        }
        else
        {
            if (mkdir(m_param.jsonPath.c_str(), 0777) == 0)
            {
                LOG_INF << "json path <" << m_param.jsonPath << "> not exist ,mkdir suc.";
            }
            else
            {
                LOG_ERR << "json path <" << m_param.jsonPath << "> not exist, mkdir failed: <" << strerror(errno) << ">.";
                return;
            }            
        }

        filestatus = { 0 };
        if (stat(strFile.c_str(), &filestatus) == -1)
        {
            // no file, and don`t care
            LOG_ERR << "video file <" << strFile << "> do not exist.";
            return;
        }

        int fileSize = filestatus.st_size / 1024 / 1024;

        Json::Value root;
        Json::Value operations;
        Json::Value insert;

        Json::Value columns;
        columns.append("camera_id");
        columns.append("capture_file_name");
        columns.append("capture_file_date");
        columns.append("capture_file_size_mb");

        Json::Value values;
        Json::Value v1;
        auto time1 = getCurDayTimeStr(1, '-', '-', '-');
        auto cameraID = std::to_string(m_param.cameraID);
        v1.append(cameraID);
        v1.append(strFile);       
        v1.append(time1);
        v1.append(std::to_string(fileSize));

        values.append(v1);

        Json::Value table = "vm_camera_status";

        insert["table"] = table;
        insert["columns"] = columns;
        insert["values"] = values;

        operations["insert"] = insert;

        root["operations"] = operations;

        LOG_INF << "insert to table <" << "vm_camera_status" << ">, camera_id <" << m_param.cameraID
            << ">, strFile <" << strFile << ">.";

        Json::FastWriter writer;
        string fileName = cameraID + "_" + time1 + "_dbrest.json";
        string newName = m_param.jsonPath + "/" + fileName;
        string tmpName = newName + ".tmp";        

        std::ofstream tmpOf(tmpName);
        if (tmpOf.is_open())
        {
            tmpOf << writer.write(root);
            tmpOf.flush();
            tmpOf.close();
            LOG_INF << "rename file <" << tmpName << "> to <" << newName << ">.";
            if (rename(tmpName.c_str(), newName.c_str()))
            {
                LOG_ERR << "can not rename file <" << tmpName << "> to <" << newName << ">, errno: <" << strerror(errno) << ">.";
            }
            else 
            {
                LOG_INF << "json save success, <" << newName << ">.";
            }
        }
        else
        {
            LOG_ERR << "can not open file <" << tmpName << "> for saving, errno: <" << strerror(errno) << ">.";
        }
    }
    catch (...)
    {
    }
}

