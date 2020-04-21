/*******************************************************************************
* Deep North Confidential
* Copyright (C) 2018 Deep North Inc. All rights reserved.
* The source code for this program is not published
* and protected by copyright controlled
*******************************************************************************/

#include <iostream>
#include <thread>

#include <boost/program_options.hpp>

#include "Utility.h"
#include "ETCDWrapper.h"
#include "AlgoParameter.h"
#include "VideoCaptureManager.h"
#include "Camera.h"
#include "Config.h"
#include "AppmgClient.h"
using namespace CameraMonitor;
void updateStatus();

int main(int argc, char **argv)
{
	try
	{        
		const static char fname[] = "main() ";
		PRINT_VERSION();
		Utility::initLogging();
		LOG_INF << fname;
		boost::program_options::options_description options("cameramonitor options");
		options.add_options()
			("help,h", "help message")
			//("etcdip,i", boost::program_options::value<std::string>(), "etcd ip")
			//("etcdport,p", boost::program_options::value<std::string>(), "etcd port")
			("type,t", boost::program_options::value<std::string>()->default_value("vlc"), "capture type:ffmpeg vlc ffmpegapi vlcapi,default is vlc.");
		boost::program_options::variables_map vm;
		boost::program_options::store(boost::program_options::parse_command_line(argc, argv, options), vm);
		if (vm.count("help"))
		{ 
			std::cout << options << std::endl;
			return -1;
		}

		CONFIG.init();
		ETCD_WRAPPER.init(CONFIG.getEtcdUrls());
		APPMG_CLIENT.init("127.0.0.1", CONFIG.getAppmgPort());
		VideoCaptureManager vcm;
		vcm.init();
		try
		{
			std::string host_etcd_path = ETCD_CAPTURE_HOST_PATH + CONFIG.getHostName();
			if (!ETCD_WRAPPER.isKeyExist(host_etcd_path))
			{
				ETCD_WRAPPER.mkdir(host_etcd_path);
			}
		}
		catch(...)
		{
			LOG_WAR << ETCD_CAPTURE_HOST_PATH << CONFIG.getHostName() << " already exist in etcd.";
		}
		
		while (true)
		{
			try
			{
				updateStatus();
				vcm.update();
			}
			catch (const std::exception& e)
			{
				LOG_ERR << fname << "ERROR:" << e.what();
			} 
			std::this_thread::sleep_for(std::chrono::seconds(CONFIG.getUpdateInterval()));
			//std::cout << "update..." << std::endl;
		}
	}
	catch (const std::exception& ex)
	{
		LOG_ERR << "ERROR:" << ex.what();
	}
	catch (...)
	{
		LOG_ERR << "unknow error.";
	}

    return 0;
}

void updateStatus()
{
	const static char fname[] = "updateStatus() ";
	LOG_INF << fname;
	std::string host_etcd_path = ETCD_CAPTURE_HOST_PATH + CONFIG.getHostName();
	if (!ETCD_WRAPPER.isKeyExist(host_etcd_path))
	{
		ETCD_WRAPPER.mkdir(host_etcd_path);
	}
	ETCD_WRAPPER.mkdir(host_etcd_path, CONFIG.getTtl());
} 