/*******************************************************************************
* Deep North Confidential
* Copyright (C) 2018 Deep North Inc. All rights reserved.
* The source code for this program is not published
* and protected by copyright controlled
*******************************************************************************/

#include <sys/types.h>
#include <sys/stat.h>
#include <string.h>
#include <memory>
#include <openssl/aes.h>
#include "AESCrypto.h"
namespace CameraMonitor
{
#define ENCODE_BLOCK_SIZE (AES_BLOCK_SIZE*2)
	//"oPysK(2sp)yske#&"
	unsigned char AESCrypto::m_key[16] = { 'o','P','y', 's', 'K', '(','2','s','p', ')', 'y', 's', 'k','e','#', '&' };
	AESCrypto::AESCrypto()
	{
		memset(m_userKey, 1, 32);
		memcpy(m_userKey, m_key, 16);
	}
	AESCrypto::~AESCrypto()
	{
	}

	int AESCrypto::encrypt(const std::string& input, std::string& output)
	{
		int result = 0;
		auto lenInput = input.length();
		auto blockCount = lenInput / AES_BLOCK_SIZE;
		auto blockRemainder = lenInput % AES_BLOCK_SIZE;
		if (blockRemainder > 0)
		{
			blockCount += 1;
		}
		for (size_t i = 0; i < blockCount; ++i)
		{
			std::string inputBlock;
			if (blockRemainder != 0 && i == blockCount - 1)
			{
				inputBlock = input.substr(i * AES_BLOCK_SIZE, blockRemainder);
			}
			inputBlock = input.substr(i * AES_BLOCK_SIZE, AES_BLOCK_SIZE);
			std::string outputBlock;
			result = aesEncrypt16(inputBlock, outputBlock);
			if (0 != result)
			{
				return result;
			}
			output += outputBlock;
		}
		return result;

	}
	int AESCrypto::decrypt(const std::string& input, std::string& output)
	{
		output.clear();
		int result = 0;
		auto lenInput = input.length();
		auto blockCount = lenInput / ENCODE_BLOCK_SIZE;
		auto blockRemainder = lenInput % ENCODE_BLOCK_SIZE;
		if (blockRemainder > 0 || blockCount < 0)
		{
			return -1;
		}
		for (size_t i = 0; i < blockCount; ++i)
		{
			std::string inputBlock;
			inputBlock = input.substr(i * ENCODE_BLOCK_SIZE, ENCODE_BLOCK_SIZE);
			std::string outputBlock;
			result = aesDecrypt16(inputBlock, outputBlock);
			if (0 != result)
			{
				return result;
			}
			output += outputBlock;
		}
		return result;
	}

	int AESCrypto::aesEncrypt16(const std::string& input, std::string& output)
	{
		AES_KEY aesKey;
		unsigned char iv[16] = { 0 };
		memcpy(iv, m_key, 16);
		if (AES_set_encrypt_key(m_userKey, 128, &aesKey) < 0)
		{
			throw std::runtime_error("AESCrypto::aesEncrypt16 AES_set_encrypt_key failed.");
		}

		size_t lenInput = input.length() < AES_BLOCK_SIZE ? AES_BLOCK_SIZE : input.length();
		std::shared_ptr<unsigned  char> inputStr(new unsigned char[lenInput], std::default_delete<unsigned char[]>());
		memset(inputStr.get(), 0, lenInput);
		strncpy((char*)inputStr.get(), input.c_str(), input.length());

		std::shared_ptr<unsigned  char> encryptStr(new unsigned char[lenInput], std::default_delete<unsigned char[]>());
		memset(encryptStr.get(), 0, lenInput);
		AES_cbc_encrypt(inputStr.get(), encryptStr.get(), lenInput, &aesKey, iv, AES_ENCRYPT);

		// conver encrypted string to hexadecimal number string 
		std::shared_ptr<unsigned  char> outputStr(new unsigned char[lenInput * 2 + 1], std::default_delete<unsigned char[]>());
		memset(outputStr.get(), 0, lenInput * 2 + 1);
		for (size_t i = 0; i < lenInput; ++i)
		{
			char xchar[3] = { 0 };
			sprintf(xchar, "%02X", encryptStr.get()[i]);
			strcat((char*)outputStr.get(), xchar);
		}

		output = std::string((char*)outputStr.get());
		return 0;
	}
	int AESCrypto::aesDecrypt16(const std::string& input, std::string& output)
	{
		unsigned char iv[16] = { 0 };
		memcpy(iv, m_key, 16);

		size_t len = input.length();
		std::shared_ptr<unsigned  char> encryptStr(new unsigned char[len / 2], std::default_delete<unsigned char[]>());
		memset(encryptStr.get(), 0, len / 2);

		// conver hexadecimal number string to encrypted string
		for (size_t i = 0; i < len; i = i + 2)
		{
			char xchar[3] = { 0 };
			int nValue = 0;
			xchar[0] = input.at(i);
			xchar[1] = input.at(i + 1);
			sscanf(xchar, "%X", &nValue);
			encryptStr.get()[i / 2] = static_cast<unsigned char>(nValue);
		}

		std::shared_ptr<unsigned  char> decryptStr(new unsigned char[len / 2 + 1], std::default_delete<unsigned char[]>());
		memset(decryptStr.get(), 0, len / 2 + 1);

		AES_KEY aesKey;
		if (AES_set_decrypt_key(m_userKey, 128, &aesKey) < 0)
		{
			throw std::runtime_error("AESCrypto::aesDecrypt16 AES_set_encrypt_key failed.");
		}

		// decrypt notice encryptStr'length is len/2
		AES_cbc_encrypt(encryptStr.get(), decryptStr.get(), len / 2, &aesKey, iv, AES_DECRYPT);
		output = std::string((char*)decryptStr.get());
		return 0;
	}
}
