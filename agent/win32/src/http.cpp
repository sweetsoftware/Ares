#include "http.h"

using namespace std;


RequestURL dissect_url(std::string url) {
	size_t found;
	RequestURL rURL;

	found = url.find("://");
	if (found != std::string::npos) {
		rURL.protocol = url.substr(0, found);
		url.erase(0, found + 3);
	}
	else {
		rURL.protocol = "http";
	}

	found = url.find(":");
	if (found != std::string::npos) {
		rURL.host = url.substr(0, found);
		url.erase(0, found + 1);
		found = url.find("/");

		if (found == std::string::npos) {
			rURL.port = atoi(url.c_str());
			rURL.path = "/";
		}
		else {
			rURL.port = atoi(url.substr(0, found).c_str());
			url.erase(0, found);
			rURL.path = url;
		}
	}

	else {
		found = url.find("/");
		if (found == std::string::npos) {
			rURL.host = url;
			rURL.port = (rURL.protocol == "http") ? 80 : 443;
			rURL.path = "/";
		}
		else {
			rURL.host = url.substr(0, found);
			url.erase(0, found);
			rURL.port = (rURL.protocol == "http") ? 80 : 443;
			rURL.path = url;
		}
	}

	return rURL;
}


std::string url_encode(const std::string& source)
{
	const char DEC2HEX[] = "0123456789ABCDEF";
	const unsigned char* pSrc = (const unsigned char *)source.c_str();
	const int SRC_LEN = source.length();
	unsigned char* const pStart = new unsigned char[SRC_LEN * 3];
	unsigned char *pEnd = pStart;
	const unsigned char* const SRC_END = pSrc + SRC_LEN;

	for (; pSrc < SRC_END; ++pSrc)
	{
		unsigned char ascii = (unsigned char)*pSrc;
		//encode this char
		*pEnd++ = '%';
		*pEnd++ = DEC2HEX[*pSrc >> 4];
		*pEnd++ = DEC2HEX[*pSrc & 0x0F];
	}

	std::string result((char *)pStart, (char *)pEnd);
	delete[] pStart;
	return result;
}


std::vector<unsigned char> http_request(const std::string& url, const std::string& method, char* const body, size_t body_size, const std::string& headers, const std::string& user_agent) {

	std::vector<unsigned char> response;

	HINTERNET hint;
	hint = InternetOpenA(user_agent.c_str(), INTERNET_OPEN_TYPE_PRECONFIG, NULL, NULL, 0);
	if (!hint) {
		return response;
	}

	HINTERNET co;
	RequestURL reqURL = dissect_url(url);
	co = InternetConnectA(hint, reqURL.host.c_str(), reqURL.port, NULL, NULL, INTERNET_SERVICE_HTTP, NULL, NULL);
	if (!co) {
		return response;
	}

	HINTERNET req;
	LPCSTR accept[] = { "*/*", NULL };

	req = HttpOpenRequestA(co, method.c_str(), reqURL.path.c_str(), 0, 0, accept, (reqURL.protocol == "https") ? 
		INTERNET_FLAG_SECURE | INTERNET_FLAG_IGNORE_CERT_CN_INVALID | INTERNET_FLAG_IGNORE_CERT_DATE_INVALID | INTERNET_FLAG_RELOAD : INTERNET_FLAG_RELOAD, 0);
	if (!req) {
		return response;
	}

	DWORD read;
	unsigned char c;

	if (HttpSendRequestA(req, headers.c_str(), headers.length(), body, body_size)) {
		while (InternetReadFile(req, (LPVOID)&c, sizeof(c), &read)) {
			if (read == 0) {
				break;
			}
			response.push_back(c);
		}
	}
	InternetCloseHandle(req);
	InternetCloseHandle(co);
	InternetCloseHandle(hint);
	return response;
}
