#include <iostream>
#include <iomanip>

#include <cpprest/http_client.h>
#include <cpprest/json.h>

#include "AppmgClient.h"
#include "Utility.h"
#include "AESCrypto.h"

namespace CameraMonitor
{
	AppmgClient::AppmgClient()
		:m_appmgBaseUrl("http://127.0.0.1:5050")
	{
	}


	AppmgClient::~AppmgClient()
	{
	}
	void AppmgClient::init(const std::string& ip, int port)
	{
		const static char fname[] = "AppmgClient::init  ";
		LOG_INF << fname;
		m_appmgBaseUrl = "http://" + ip + ":" + std::to_string(port);
		LOG_INF << "m_appmgBaseUrl <" << m_appmgBaseUrl << ">.";
	}
	bool AppmgClient::isRegisted(
		const std::string& name,
		const std::string& runas,
		const std::string& cmdline)
	{
		const static char fname[] = "AppmgClient::isRegisted  ";
		LOG_INF << fname << "name <" << name << ">.";
		auto jsonValue = query();
		auto arr = jsonValue.as_array();
		for (auto iter = arr.begin(); iter != arr.end(); iter++)
		{
			auto jobj = iter->as_object();
			if (GET_JSON_STR_VALUE(jobj, APPMG_NAME) == name 
				&& GET_JSON_STR_VALUE(jobj, APPMG_CMDLINE) == cmdline
				&& GET_JSON_STR_VALUE(jobj, APPMG_RUNAS) == runas)
			{
				return true;
			}
		}
		return false;
	}

	int AppmgClient::createToken(std::string& token)
	{
		auto now = std::time(nullptr);
		auto tm = *std::localtime(&now);
		std::stringstream ss;
		ss << std::put_time(&tm, "%Y-%m-%d %H:%M:%S") << std::endl;
		std::string tokenPlain = "deepnorth_passwd" + ss.str();
		return AESCRYPTO.encrypt(tokenPlain, token);
	}

	void AppmgClient::regist(
		const std::string& name,
		const std::string& runas,
		const std::string& cmdline,
		const std::string& workdir,
		const std::string& startTime,
		const std::string& dailyStart,
		const std::string& dailyEnd,
		const std::string& env,
		int interval,
		int extraTime,
		int active)
	{
		const static char fname[] = "AppmgClient::regist  ";
		LOG_WAR << fname << "name <" << name << "> runas <" << runas << "> cmdline <"
			<< cmdline << "> workdir <" << workdir << "> startTime <" << startTime << "> interval <"
			<< interval << "> extraTime <" << extraTime << "> active <" << active << ">.";
		web::json::value obj;
		obj[APPMG_NAME] = web::json::value::string(name);
		obj[APPMG_CMDLINE] = web::json::value::string(cmdline);
		obj[APPMG_RUNAS] = web::json::value::string(runas);
		obj[APPMG_WORKDIR] = web::json::value::string(workdir);
		obj[APPMG_ACTIVE] = web::json::value::number(active);
		if (!startTime.empty())
		{
			obj[APPMG_START_TIME] = web::json::value::string(startTime);
		}
		if (interval > 0)
		{
			obj[APPMG_START_INTERVAL_SECONDS] = web::json::value::number(interval);
		}

		if (extraTime > 0)
		{
			obj[APPMG_TIMEOUT_FOR_START_INTERVAL] = web::json::value::number(extraTime);
		}
		obj[APPMG_KEEP_RUNNING] = web::json::value::boolean(true);

		if (!dailyStart.empty() && !dailyEnd.empty())
		{
			web::json::value objDailyLimitation;
			objDailyLimitation[APPMG_DAILY_START] = web::json::value::string(dailyStart);
			objDailyLimitation[APPMG_DAILY_END] = web::json::value::string(dailyEnd);
			obj[APPMG_DAILY_LIMITATION] = objDailyLimitation;
		}
		if (!env.empty())
		{
			std::vector<std::string> envs;
			Utility::splitString(env, envs, ":");
			if (envs.size())
			{
				web::json::value objEnvs = web::json::value::object();
				std::for_each(envs.begin(), envs.end(), [&objEnvs](std::string e)
				{
					std::vector<std::string> envVec;
					Utility::splitString(e, envVec, "=");
					if (envVec.size() == 2)
					{
						objEnvs[GET_STRING_T(envVec.at(0))] = web::json::value::string(GET_STRING_T(envVec.at(1)));
					}
				});
				obj[APPMG_ENV] = objEnvs;
			}
		}
		httpRequest("/reg", obj, web::http::methods::PUT);
	}

	void AppmgClient::unregist(const std::string& name)
	{
		const static char fname[] = "AppmgClient::unregist  ";
		LOG_WAR << fname << "name <" << name << ">.";
		web::json::value obj;
		obj[APPMG_NAME] = web::json::value::string(name);
		httpRequest("/unreg", obj, web::http::methods::DEL);
	}

	void AppmgClient::httpRequest(const std::string& url, web::json::value objData, web::http::method methodReq)
	{
		const static char fname[] = "AppmgClient::httpRequest  ";
		LOG_INF << fname << "url <" << url << ">.";
		web::http::client::http_client client(m_appmgBaseUrl);
		web::http::http_request request;
		request.set_method(methodReq);
		std::string token;
		createToken(token);
		request.headers().add("token", token);
		request.set_request_uri(web::uri(GET_STRING_T(url)));
		request.set_body(objData);
		web::http::http_response response = client.request(request).get();
		auto bodyStr = response.extract_utf8string(true).get();
		LOG_INF << "http response:" << bodyStr;
	}

	web::json::value AppmgClient::query()
	{
		const static char fname[] = "AAppmgClient::query()  ";
		LOG_INF << fname;
		const std::string queryUrl = m_appmgBaseUrl + "/query";
		web::http::client::http_client client(GET_STRING_T(queryUrl));
		web::http::http_response response = client.request(web::http::methods::GET).get();
		auto jsonValue = response.extract_json(true).get();
		LOG_INF << "query result:" << jsonValue ;
		return jsonValue;
	}
}

