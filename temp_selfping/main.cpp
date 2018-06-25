#include "mbed.h"
#include "EthernetInterface.h"
#include "UDPSocket.h"
#include "SocketAddress.h"

#define PORT 60001
#define TIMEOUT_MS 1000

EthernetInterface* ethernet;
UDPSocket* socket;
SocketAddress address;

Serial PC(USBTX, USBRX, 460800);

int main(){

	// Set up network
	ethernet = new EthernetInterface;
	printf("\n\rConnecting...");
	int result = ethernet->connect();
	
	if(result < 0 ){
		printf(" Failed. Rebooting to try again\n\n\r");
		wait(0.001);
		NVIC_SystemReset();
	} else {
		printf(" Done");
	}

	printf("\n\rSetting up socket...");
	socket = new UDPSocket(ethernet);
	socket->bind(PORT);
	socket->set_timeout(TIMEOUT_MS); // ms
	printf(" Done");

	// Stay in loop:
		// Send ping
		// Listen for ping
		// Notify of result
		// Wait
	
	uint32_t count;
	while(true){
		
		printf("\n\rConnection status: ");

		switch(ethernet->get_connection_status()){
			case NSAPI_STATUS_LOCAL_UP:
				printf("LOCAL_UP");
				break;

			case NSAPI_STATUS_GLOBAL_UP:
				printf("GLOBAL_UP");
				break;

			case NSAPI_STATUS_DISCONNECTED:
				printf("DISCONNECTED");
				break;

			case NSAPI_STATUS_CONNECTING:
				printf("CONNECTING");
				break;

			case NSAPI_STATUS_ERROR_UNSUPPORTED:
				printf("UNSUPPORTED");
				break;

			default:
				printf("UWOTM8");
				

		}

	}

	return 0;
}
