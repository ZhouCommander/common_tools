#ifndef __CAPTURE_SENDMQ_H__
#define __CAPTURE_SENDMQ_H__

#include "capture_common.h"

#include <map>
#include <jsoncpp/json/json.h>

#include <amqp.h>
#include <amqp_tcp_socket.h>

class CaptureSendMQ
{
public:
    CaptureSendMQ();
    virtual ~CaptureSendMQ();

    virtual void init(const string &strMQUrl, const string &strMQRoot, const string &strQueueName, const string strCacheDir="");
    virtual RetCode_E sendMQ(CaptureParam_ST &param, string &strFile, time_t capDur);

private:
	//rabbitmq uri
	//user:passwd@host:port
    string m_strMQUrl;
    string m_strMQRoot;
    string m_strQueueName;
	string m_strUser;
	string m_strPasswd;
	string m_host;
	int    m_port;

    string m_strCacheDir;

    bool send(amqp_connection_state_t& conn, int cameraID, string &capTime, int capDur, string &strFile);
    std::map<time_t, string> getAllMsg(int cameraID);
    Json::Value readMsgFromFile(string strFileName);
    void saveMsg2File(int cameraID, string &capTime, int capDur, string &strFileName);
    Json::Value getMsgJson(int cameraID, string &capTime, int capDur, string &strFileName);
	void getMQInfoFromURI(const string& strUri,string& host,int& port,string& user,string& passwd);

};

#endif

