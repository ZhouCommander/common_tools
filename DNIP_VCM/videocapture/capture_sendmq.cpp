#include "capture_sendmq.h"

#include <dirent.h>
#include <fstream>
#include <utility>



#define TAG "<CaptureSendMQ>"

static const char CACHE_DIR[] = "cache_";

CaptureSendMQ::CaptureSendMQ()
:m_port(5672)
{
}

CaptureSendMQ::~CaptureSendMQ()
{
}

void CaptureSendMQ::init(const string &strMQUrl, const string &strMQRoot, const string &strQueueName, const string strCacheDir)
{
    const static char fnName[] = "CaptureSendMQ::init()";
    m_strMQUrl = strMQUrl;
    m_strMQRoot = strMQRoot;
    m_strQueueName = strQueueName;
	getMQInfoFromURI(m_strMQUrl, m_host, m_port, m_strUser, m_strPasswd);
    if(strCacheDir.empty())
    {
        m_strCacheDir = getBaseDir() + string("/") + string(CACHE_DIR);
    }
    else
    {
        m_strCacheDir = strCacheDir;
    }   
    LOG_INF << fnName << " m_strMQUrl<" << m_strMQUrl << ">, strMQRoot <" << strMQRoot << ">, strQueueName <" << strQueueName << ">, m_strCacheDir <" << m_strCacheDir << ">";
}

RetCode_E CaptureSendMQ::sendMQ(CaptureParam_ST &param, string &strFile, time_t capDur)
{
	string capTime = getDayTimeFromString(strFile);
    if(m_strMQUrl.empty() || m_strMQRoot.empty() || m_strQueueName.empty())
    {
        LOG_INF << " sendMQ find MQUrl or MQRoot or QueueName is empty, not send";
		saveMsg2File(param.cameraID, capTime, (int)capDur, strFile);
	    return RET_STOPED;
    }

	amqp_connection_state_t conn = amqp_new_connection();
	amqp_socket_t* socket = amqp_tcp_socket_new(conn);

	if (!socket) 
	{
		LOG_INF << " sendMQ creating TCP socket failed, not send";
		saveMsg2File(param.cameraID, capTime, (int)capDur, strFile);
		return RET_STOPED;
	}

	int status = amqp_socket_open(socket, m_host.c_str(), m_port);
	if (status) 
	{
		LOG_INF << " sendMQ opening TCP socket failed, not send";
		saveMsg2File(param.cameraID, capTime, (int)capDur, strFile);
		return RET_STOPED;
	}
	amqp_rpc_reply_t reply = amqp_login(conn, "/", 0, 131072, 0, AMQP_SASL_METHOD_PLAIN, "guest", "guest");
	if (NULL == amqp_channel_open(conn, 1))
	{
		LOG_INF << " sendMQ Opening channel failed, not send";
		saveMsg2File(param.cameraID, capTime, (int)capDur, strFile);
		return RET_STOPED;
	}
	reply = amqp_get_rpc_reply(conn);
    amqp_queue_declare(conn, 1, amqp_cstring_bytes(m_strQueueName.c_str()), 0, 1, 0, 0, amqp_empty_table);

	// read and send failed msg
	std::map<time_t, string> mapFile = getAllMsg(param.cameraID);
	for (std::map<time_t, string>::iterator iter = mapFile.begin(); iter != mapFile.end(); ++iter)
	{
		Json::Value jsonMsg = readMsgFromFile(iter->second);
		int cameraID = jsonMsg["camera_id"].asInt();
		string strCapTime = jsonMsg["capture_time"].asString();
		int captureDur = jsonMsg["capture_duration_seconds"].asInt();
		string strFilePath = jsonMsg["file_path"].asString();
		if (send(conn, cameraID, strCapTime, captureDur, strFilePath))
		{
			ACE_OS::unlink(iter->second.c_str());
			LOG_INF << " remove failed msg is <"<< iter->second << ">.";
		}
	}

	// send cur msg

	if (!send(conn, param.cameraID, capTime, (int)capDur, strFile))
	{
		saveMsg2File(param.cameraID, capTime, (int)capDur, strFile);
	}

	amqp_channel_close(conn, 1, AMQP_REPLY_SUCCESS);
	amqp_connection_close(conn, AMQP_REPLY_SUCCESS);
	amqp_destroy_connection(conn);

    LOG_INF << " sendMQ end\r\n";
    return RET_SUCCESS;
}

bool CaptureSendMQ::send(amqp_connection_state_t& conn, int cameraID, string &capTime, int capDur, string &strFile)
{
    const static char fnName[] = "CaptureSendMQ::send  ";
    LOG_INF << fnName << "cameraID <"<< cameraID <<">, capTime <" << capTime << ">, capDur <" << capDur << ">, strFile <" << strFile << ">.";
    string strCapTime = getDayTimeFromString(strFile);
    string strMsgBody = getMsgJson(cameraID, strCapTime, capDur, strFile).toStyledString();
	amqp_basic_properties_t props;
	props._flags = AMQP_BASIC_CONTENT_TYPE_FLAG | AMQP_BASIC_DELIVERY_MODE_FLAG;
	props.content_type = amqp_cstring_bytes("text/plain");
	props.delivery_mode = 2; /* persistent delivery mode */
	bool bRet = false;
	if (AMQP_STATUS_OK == amqp_basic_publish(conn, 1, amqp_cstring_bytes(""), amqp_cstring_bytes(m_strQueueName.c_str()), 0, 0, &props, amqp_cstring_bytes(strMsgBody.c_str())))
	{
		bRet = true;
	}
    LOG_INF << " sent, strMsgBody <" << strMsgBody <<">, bRet <"<< bRet <<">.";
    return bRet;
}

std::map<time_t, string> CaptureSendMQ::getAllMsg(int cameraID)
{
    const static char fnName[] = "CaptureSendMQ::getAllMsg()  ";
    LOG_INF << fnName << "cameraID <" << cameraID << ">";
    string msgDir = m_strCacheDir + string("/") + to_string(cameraID);
    std::map<time_t, string> mapFile;

    DIR* dir = opendir(msgDir.c_str());
    if (dir != NULL)
    {
        struct dirent* rent = NULL;
        while ((rent = readdir(dir)))
        {
            try
            {
                if (!(rent->d_type == DT_DIR))
                {
                    string strFileName = rent->d_name;
                    string strName = strFileName.substr(0, strFileName.rfind("."));
                    mapFile.insert(std::pair<time_t, string>(atoi(strName.c_str()), msgDir + string("/") + strFileName));
                }
            }
            catch (const std::exception& e)
            {
                LOG_ERR << " find incorrect file: <" << rent->d_name << ">, error: <" << e.what() << ">.";
            }
            catch (...)
            {
                LOG_ERR << " getAllMsg find unknown exception";
            }
        }
        closedir(dir);
    }

    return mapFile;
}

Json::Value CaptureSendMQ::readMsgFromFile(string strFileName)
{
    Json::CharReaderBuilder reader;
    Json::Value jsonMsg;
    std::ifstream is;
    is.open(strFileName.c_str(), std::ios::binary);
    JSONCPP_STRING errs;
    parseFromStream(reader, is, &jsonMsg, &errs);
    is.close();
    return jsonMsg;
}

void CaptureSendMQ::saveMsg2File(int cameraID, string &capTime, int capDur, string &strFileName)
{
    string msgDir = m_strCacheDir + string("/") + to_string(cameraID);
    mkdirs(msgDir, DIR_MODE);

    time_t curTime = time(NULL);
    string filename = msgDir + string("/") + to_string(curTime) + string(".json");

    std::ofstream ofs;
    ofs.open(filename);
    ofs << getMsgJson(cameraID, capTime, capDur, strFileName).toStyledString();
    ofs.close();
    LOG_INF << " save msg <"<< cameraID <<", "<< capTime <<", "<< capDur <<", "<< strFileName <<"> to file <"<< filename <<">.";
}

Json::Value CaptureSendMQ::getMsgJson(int cameraID, string &capTime, int capDur, string &strFileName)
{
    Json::Value jsonMsg;
    jsonMsg["camera_id"] = cameraID;
    jsonMsg["capture_time"] = capTime;
    jsonMsg["capture_duration_seconds"] = capDur;
    jsonMsg["file_path"] = strFileName;
    return jsonMsg;
}

void CaptureSendMQ::getMQInfoFromURI(const string& strUri, string& host, int& port, string& user, string& passwd)
{
    const static char fnName[] = "CaptureSendMQ::getMQInfoFromURI()  ";
    LOG_INF << fnName;
	if (string::npos == strUri.find('@'))
	{
		//host:port
		std::vector<string> vecHostPort;
		splitString(m_strMQUrl, vecHostPort, ":");
		if (vecHostPort.size() == 2)
		{
			host = vecHostPort.at(0);
			std::string::size_type sz;
			port = std::stoi(vecHostPort.at(1), &sz);
			user = "guest";
			passwd = "guest";
		}
	}
	else
	{
		std::vector<string> vecUserPasswdHostPort;
		splitString(m_strMQUrl, vecUserPasswdHostPort, "2");
		if (vecUserPasswdHostPort.size() == 2)
		{
			string strUserPasswd = vecUserPasswdHostPort.at(0);
			std::vector<string> vecUserPasswd;
			splitString(strUserPasswd, vecUserPasswd, ":");
			if (vecUserPasswd.size() == 2)
			{
				user = vecUserPasswd.at(0);
				passwd = vecUserPasswd.at(1);
			}
			string strHostPort = vecUserPasswdHostPort.at(1);
			std::vector<string> vecHostPort;
			splitString(strHostPort, vecHostPort, ":");
			if (vecHostPort.size() == 2)
			{
				host = vecHostPort.at(0);
				std::string::size_type sz;
				port = std::stoi(vecHostPort.at(1), &sz);
			}	
		}
	}
}

