/*******************************************************************************
* Deep North Confidential
* Copyright (C) 2018 Deep North Inc. All rights reserved.
* The source code for this program is not published
* and protected by copyright controlled
*******************************************************************************/

#include "Utility.h"
#include "AlgoParameter.h"
#include "ETCDWrapper.h"
#include "Config.h"
namespace CameraMonitor
{
	AlgoParameter::AlgoParameter()
	{
		m_data.clear();
	}


	AlgoParameter::~AlgoParameter()
	{
	}

	void AlgoParameter::fromEtcd(std::vector<std::map<std::string, std::string> >& data)
	{
		const static char fname[] = "AlgoParameter::fromEtcd  ";
		LOG_INF << fname;
		ETCD_WRAPPER.toVector("/db/" + CONFIG.getAlgoParaTableName(),data);
	}
	void AlgoParameter::update()
	{
		const static char fname[] = "AlgoParameter::update()  ";
		LOG_INF << fname;
		std::vector<std::map<std::string, std::string>> data;
		fromEtcd(data);	
		m_data = data;
	}

	std::vector<std::map<std::string, std::string> > AlgoParameter::getData()
	{
		return m_data;
	}

}
