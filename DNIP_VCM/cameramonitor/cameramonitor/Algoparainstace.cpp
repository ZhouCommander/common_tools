/*******************************************************************************
* Deep North Confidential
* Copyright (C) 2018 Deep North Inc. All rights reserved.
* The source code for this program is not published
* and protected by copyright controlled
*******************************************************************************/
#include "Algoparainstace.h"
#include "Utility.h"
#include "ETCDWrapper.h"
#include "Config.h"
namespace CameraMonitor
{
	Algoparainstace::Algoparainstace()
	{
		
	}


	Algoparainstace::~Algoparainstace()
	{
	}

	void Algoparainstace::fromEtcd(std::vector<std::map<std::string, std::string> >& data)
	{
		const static char fname[] = "Algoparainstace::fromEtcd  ";
		LOG_INF << fname ;
		ETCD_WRAPPER.toVector("/db/" + CONFIG.getAlgoParaInstance(), data);
	}
	void Algoparainstace::update()
	{
		const static char fname[] = "Algoparainstace::update()  ";
		LOG_INF << fname;
		std::vector<std::map<std::string, std::string> > data;
		fromEtcd(data);
		m_data = data;
	}

	std::vector<std::map<std::string, std::string> > Algoparainstace::getData()
	{
		return m_data;
	}
}

