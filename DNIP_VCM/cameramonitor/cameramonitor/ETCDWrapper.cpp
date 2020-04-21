/*******************************************************************************
* Deep North Confidential
* Copyright (C) 2018 Deep North Inc. All rights reserved.
* The source code for this program is not published
* and protected by copyright controlled
*******************************************************************************/
#include <exception>
#include <thread>
#include "ETCDWrapper.h"
#include "Utility.h"
namespace CameraMonitor
{
	ETCDWrapper::ETCDWrapper()
	{
	}
	void ETCDWrapper::init(const std::string& urls)
	{
		const static char fname[] = "ETCDWrapper::init  ";
		//LOG_INF << fname << "ip <" << ip << "> port <" << port << ">." << std::endl;
		//m_baseUrl = "http://" + ip + ":" + port + "/v2/keys";

		std::vector<std::string> vectorUrls;
		Utility::splitString(urls, vectorUrls,",");
		std::deque<std::string> etcdUrls;
		for (auto url : vectorUrls)
		{
			etcdUrls.push_back(url);
		}
		if (etcdUrls.size() > 0)
		{
			m_baseUrl = etcdUrls.front() + "/v2/keys";
		}
		m_etcdUrls = etcdUrls;
	}

	ETCDWrapper::~ETCDWrapper()
	{
	}
	bool ETCDWrapper::isKeyExist(const std::string& key)
	{
		const static char fname[] = "ETCDWrapper::isKeyExist  ";
		LOG_INF << fname << "key <" << key << "> ";
		std::string path = key;
		web::http::http_request request(web::http::methods::GET);
		std::string result;
		httpRequest(path, request, result);;
		std::string value = GET_STRING_T(result);
		LOG_INF << "value <" << value << "> ";
		auto jval = web::json::value::parse(value);
		web::json::object jobj = jval.as_object();
		int errorCode = GET_JSON_INT_VALUE(jobj, "errorCode");
		if (0 == errorCode)
		{
			return true;
		}
		else
		{
			return false;
		}
	}
	void ETCDWrapper::get(const std::string& key, std::string& value)
	{
		const static char fname[] = "ETCDWrapper::get  ";
		LOG_INF << fname << "key <" << key << "> ";
		std::string path = key;
		std::ifstream jsonFile(key);
		if (!jsonFile.is_open())
		{
			LOG_INF << "ERROR can not open configuration file <" << path << ">";

		}
		else
		{
			std::string str((std::istreambuf_iterator<char>(jsonFile)), std::istreambuf_iterator<char>());
			jsonFile.close();
			LOG_INF << "Read config: " << str;
			value = str;
		}
		
	}
	void ETCDWrapper::set(const std::string& key, const std::string& value, const int ttl)
	{
		const static char fname[] = "ETCDWrapper::set  ";
		LOG_INF << fname << "key <" << key << "> value <" << value << "> ttl <" << ttl << ">.";
		std::string path = key;
		web::http::http_request request(web::http::methods::PUT);
		std::string data = "value=" + web::uri::encode_data_string(value);
		if (ttl > 0)
		{
			data = data + "&ttl=" + std::to_string(ttl);
		}
		request.set_body(data, "application/x-www-form-urlencoded");
		std::string result;
		httpRequest(path, request, result);
		handleError("etcd set key <" + key + "> value <" + value + "> failed:", GET_STRING_T(result));
	}

	void ETCDWrapper::mkdir(const std::string& dir, const int ttl)
	{
		const static char fname[] = "ETCDWrapper::mkdir  ";
		LOG_INF << fname << "dir <" << dir <<  "> ttl <" << ttl << ">.";
		std::string path = dir;
		web::http::http_request request(web::http::methods::PUT);
		std::string data = "dir=true";
		if (ttl > 0)
		{
			data = data + "&ttl=" + std::to_string(ttl);
			data += "&prevExist=true";
		}
		request.set_body(data, "application/x-www-form-urlencoded");
		std::string result;
		httpRequest(path, request, result);
		handleError("etcd mkdir <" + dir + "> failed:", GET_STRING_T(result));
	}

	void ETCDWrapper::del(const std::string& key)
	{
		const static char fname[] = "ETCDWrapper::del  ";
		LOG_INF << fname << "key <" << key << ">.";
		const std::string args = "?dir=false&recursive=true";
		std::string path = key + args;
		web::http::http_request request(web::http::methods::DEL);
		std::string result;
		httpRequest(path, request, result);
		handleError("etcd del key <" + key + "> failed:", GET_STRING_T(result));
	}

	void ETCDWrapper::handleError(const std::string& errorMsg, const std::string& errorData)
	{
		auto jval = web::json::value::parse(errorData);
		web::json::object jobj = jval.as_object();
		int errorCode = GET_JSON_INT_VALUE(jobj, "errorCode");
		if (0 != errorCode)
		{
			const static char fname[] = "ETCDWrapper::handleError  ";
			LOG_ERR << fname << errorMsg << errorData ;
			throw std::invalid_argument(errorMsg + errorData);
		}
	}

	void ETCDWrapper::toVector(const std::string& rootKey, std::vector< std::map<std::string, std::string> >& data)
	{
		const static char fname[] = "ETCDWrapper::toVector  ";
		LOG_INF << fname;
		std::string rootValue;
		get(rootKey, rootValue);
		auto jval = web::json::value::parse(GET_STRING_T(rootValue));
		web::json::object jobj = jval.as_object();
		auto node = jobj.at(GET_STRING_T("node")).as_object();
		if (HAS_JSON_FIELD(node, GET_STRING_T("nodes")))
		{
			auto nodes = node.at(GET_STRING_T("nodes")).as_array();
			for (auto iter = nodes.begin(); iter != nodes.end(); ++iter)
			{
				web::json::object nodeObj = iter->as_object();
				std::string nodeKey = GET_JSON_STR_VALUE(nodeObj, "key");
				LOG_INF << "nodeKey <" << nodeKey << ">.";
				std::string itemValue;
				get(nodeKey, itemValue);
				auto jvalItem = web::json::value::parse(GET_STRING_T(itemValue));
				web::json::object jobjItem = jvalItem.as_object();
				auto nodeItem = jobjItem.at(GET_STRING_T("node")).as_object();
				auto nodesItem = nodeItem.at(GET_STRING_T("nodes")).as_array();
				std::map<std::string, std::string> mapItem;
				for (auto iterItem = nodesItem.begin(); iterItem != nodesItem.end(); ++iterItem)
				{
					web::json::object nodeObjItem = iterItem->as_object();
					std::string nodeKeyItem = GET_JSON_STR_VALUE(nodeObjItem, "key");
					//remvoe / 
					std::string columnName = nodeKeyItem.substr(nodeKey.length() + 1, nodeKeyItem.length() - nodeKey.length() - 1);
					std::string nodeValueItem = GET_JSON_STR_VALUE(nodeObjItem, "value");
					LOG_INF << "columnName <" << columnName << "> value <" << nodeValueItem << ">.";
					mapItem.insert(std::pair<std::string, std::string>(columnName, nodeValueItem));
				}
				data.push_back(mapItem);
			}
		}
	}

	void ETCDWrapper::httpRequest(
		const std::string& path,
		const web::http::http_request& req,
		std::string& result)
	{
		const static char fname[] = "ETCDWrapper::httpReques  ";
		result.clear();
		bool status = false;
		std::deque<std::string> urls = m_etcdUrls;
		do
		{
			try
			{
				LOG_INF << fname << "etcd baseUrl" << "<"  << m_baseUrl << ">.";
				web::http::client::http_client client(m_baseUrl + path);
				web::http::http_response response = client.request(req).get();
				result = response.extract_utf8string(true).get();
				status = true;
			}
			catch (std::exception& e)
			{
				LOG_WAR << fname << "access etcd exception: " << e.what() << ".";
				if (!urls.empty())
				{
					std::string url;
					do
					{
						url = urls.front() + "/v2/keys";
						urls.pop_front();

					} while (!urls.empty() && url == m_baseUrl);
					m_baseUrl = url ;
				}
				std::this_thread::sleep_for(std::chrono::seconds(3));
			}
		} while (!status && !m_baseUrl.empty());

		if (!status)
		{
			LOG_ERR << fname << "failed to access etcd.";
		}

	}
}
