/*******************************************************************************
* Deep North Confidential
* Copyright (C) 2018 Deep North Inc. All rights reserved.
* The source code for this program is not published
* and protected by copyright controlled
*******************************************************************************/
#ifndef CAMERA_DEFINITION
#define CAMERA_DEFINITION
#include <map>
#include <vector>
#include <string>
namespace CameraMonitor
{
	class Camera
	{
	public:
		Camera();
		virtual ~Camera();
		void update();
		std::vector<std::map<std::string, std::string> > getData();
	private:
		void fromEtcd(std::vector<std::map<std::string, std::string> >& data);
		std::vector<std::map<std::string, std::string> > m_data;
	};
}

#endif

