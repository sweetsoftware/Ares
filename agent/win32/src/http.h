#pragma once

#include <string>
#include <vector>
#include <Windows.h>
#include <winsock.h>
#include <wininet.h>
#include <cstdlib>
#include <cstdio>

struct RequestURL {
	std::string protocol;
	std::string host;
	int port;
	std::string path;
};

RequestURL dissect_url(std::string url);

std::string url_encode(const std::string& source);

std::vector<unsigned char> http_request(const std::string& url, const std::string& method = "GET", char* const body = NULL, size_t body_size = 0, const std::string& headers = "", const std::string& user_agent = "Mozilla/4.0 (compatible)");
