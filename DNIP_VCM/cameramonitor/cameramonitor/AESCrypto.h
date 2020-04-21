
/*******************************************************************************
* Deep North Confidential
* Copyright (C) 2018 Deep North Inc. All rights reserved.
* The source code for this program is not published
* and protected by copyright controlled
*******************************************************************************/
#ifndef AESCRYPTO_DEFINITION
#define AESCRYPTO_DEFINITION
#include <boost/serialization/singleton.hpp>
#include <iostream>
#include <string>

//////////////////////////////////////////////////////////////////////////
// aes encrypt and decrypt 
// after encrypt encode binary data to HEX
//////////////////////////////////////////////////////////////////////////
namespace CameraMonitor
{
	class AESCrypto :public boost::serialization::singleton<AESCrypto>
	{
	public:
		AESCrypto();
		~AESCrypto();
		int encrypt(const std::string& input, std::string& output);
		int decrypt(const std::string& input, std::string& output);

	private:
		int aesEncrypt16(const std::string& input, std::string& output);
		int aesDecrypt16(const std::string& input, std::string& output);
		// AES_BLOCK_SIZE = 16
		static unsigned char m_key[16];
		//AES_BLOCK_SIZE*2
		unsigned char m_userKey[32];
	};
#define AESCRYPTO AESCrypto::get_mutable_instance()
}

#endif