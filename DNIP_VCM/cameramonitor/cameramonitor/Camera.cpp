/*******************************************************************************
* Deep North Confidential
* Copyright (C) 2018 Deep North Inc. All rights reserved.
* The source code for this program is not published
* and protected by copyright controlled
*******************************************************************************/
#include "Camera.h"
#include "Utility.h"
#include "ETCDWrapper.h"
#include "Config.h"
namespace CameraMonitor
{
	Camera::Camera()
	{
	}


	Camera::~Camera()
	{
	}

	void Camera::fromEtcd(std::vector<std::map<std::string, std::string> >& data)
	{
		const static char fname[] = "Camera::fromEtcd  ";
		LOG_INF << fname ;
		ETCD_WRAPPER.toVector("/db/" + CONFIG.getCameraTableName(), data);
	}
	void Camera::update()
	{
		const static char fname[] = "Camera::update()  ";
		LOG_INF << fname;
		std::vector<std::map<std::string, std::string> > data;
		fromEtcd(data);
		m_data = data;
	}

	std::vector<std::map<std::string, std::string> > Camera::getData()
	{
		return m_data;
	}
}

