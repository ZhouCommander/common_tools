/*******************************************************************************
* Deep North Confidential
* Copyright (C) 2018 Deep North Inc. All rights reserved.
* The source code for this program is not published
* and protected by copyright controlled
*******************************************************************************/
#ifndef ETCDWRAPPER_DEFINITION
#define ETCDWRAPPER_DEFINITION
#include <string>
#include <vector>
#include <deque>
#include <string>
#include <map>
#include <boost/serialization/singleton.hpp>

#include <cpprest/http_client.h>
#include <cpprest/json.h>

namespace CameraMonitor
{
	class ETCDWrapper :public boost::serialization::singleton<ETCDWrapper>
	{
	public:
		ETCDWrapper();
		virtual ~ETCDWrapper(); 
		void init(const std::string& urls);
		bool isKeyExist(const std::string& key);
		void get(const std::string& key, std::string& value);
		//ttl="" no ttl.
		void set(const std::string& key, const std::string& value, const int ttl = -1);
		void del(const std::string& key);
		void mkdir(const std::string& dir, const int ttl = -1);
		void toVector(const std::string& rootKey, std::vector< std::map<std::string, std::string> >& data);
	private:
		std::string m_baseUrl;
		std::deque<std::string> m_etcdUrls;
		void handleError(const std::string& errorMsg, const std::string& errorData);
		void httpRequest(
			const std::string& path, 
			const web::http::http_request& req,
			std::string& result);
	};
#define ETCD_WRAPPER ETCDWrapper::get_mutable_instance()
}
#endif
