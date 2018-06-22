////////////////////////////////////////////////////////////////////////////////
// Project: Fanclub Mark II "Bootloader" // File: BTCommunicator.cpp          //
//----------------------------------------------------------------------------//
// CALIFORNIA INSTITUTE OF TECHNOLOGY // GRADUATE AEROSPACE LABORATORY //     //
// CENTER FOR AUTONOMOUS SYSTEMS AND TECHNOLOGIES                             //
//----------------------------------------------------------------------------//
//      ____      __      __  __      _____      __      __    __    ____     //
//     / __/|   _/ /|    / / / /|  _- __ __\    / /|    / /|  / /|  / _  \    //
//    / /_ |/  / /  /|  /  // /|/ / /|__| _|   / /|    / /|  / /|/ /   --||   //
//   / __/|/ _/    /|/ /   / /|/ / /|    __   / /|    / /|  / /|/ / _  \|/    //
//  / /|_|/ /  /  /|/ / // //|/ / /|__- / /  / /___  / -|_ - /|/ /     /|     //
// /_/|/   /_/ /_/|/ /_/ /_/|/ |\ ___--|_|  /_____/| |-___-_|/  /____-/|/     //
// |_|/    |_|/|_|/  |_|/|_|/   \|___|-    |_____|/   |___|     |____|/       //
//                   _ _    _    ___   _  _      __   __                      //
//                  | | |  | |  | T_| | || |    |  | |  |                     //
//                  | _ |  |T|  |  |  |  _|      ||   ||                      //
//                  || || |_ _| |_|_| |_| _|    |__| |__|                     //
//                                                                            //
//----------------------------------------------------------------------------//
// Alejandro A. Stefan Zavala // <astefanz@berkeley.com> //                   //
////////////////////////////////////////////////////////////////////////////////

#include "BTCommunicator.h"


// HTTP Client:
#include "easy-connect.h"
#include "http_request.h"


//// FUNCTION DEFINITIONS //////////////////////////////////////////////////////

BTCommunicator::BTCommunicator(int socketTimeoutMS, int maxRebootTimeouts,
	uint16_t listenerPort):
	listenerSocket(),
	masterBroadcastAddress(),
	listenerPort(listenerPort),
	misoPort(0),
	socketTimeoutMS(socketTimeoutMS), maxRebootTimeouts(maxRebootTimeouts),
	networkError(false){

	this->passwordBuffer[0] = '\0';
	this->filename[0] = '\0';

	int result = -666; // Keep track of error codes;

	// Initialize network ------------------------------------------------------

	this->ethernet = easy_connect(true);
	/*
	// Ethernet interface:
	result = int(this->ethernet->connect());
	if (result != 0) {
		printf("\tERROR initializing ethernet interface (%d)\n\r", result);
		this->networkError = true;
		return;
	}
	*/
	// Sockets:	
	this->listenerSocket.open(this->ethernet);
	this->listenerSocket.bind(listenerPort);
	this->listenerSocket.set_timeout(socketTimeoutMS);

	printf("\tConnected as %s (%d)\n\r", 
		this->ethernet->get_ip_address(), this->listenerPort);

	return;
} // End constructor

BTCommunicator::~BTCommunicator(void){
	
	// Close sockets and network interface:
	
	/*
	this->listenerSocket.close();
	this->ethernet->disconnect();
	*/

} // End destructor

BTCode BTCommunicator::listen(uint16_t bufferSize){
	
	// Listen for broadcasts until either a connection is secured or the network
	// times out...

	int timeouts = 0;
	int bytesReceived;
	char* misoBuffer = new char[bufferSize];
	char* mosiBuffer = new char[bufferSize];
	BTCode returnCode = REBOOT;

	do {
		
		// Listen for broadcast:
		bytesReceived = this->listenerSocket.recvfrom(
			&masterBroadcastAddress, mosiBuffer, bufferSize); 

		// Check for errors:
		if (bytesReceived == NSAPI_ERROR_WOULD_BLOCK){
			// Timed out
			printf("\tWaiting... [%2d/%2d]\n\r", 
				timeouts, this->maxRebootTimeouts);

			timeouts++;
			if (timeouts >= this->maxRebootTimeouts){
				printf("\tERROR: Timeout limit reached while listening\n\r");
				returnCode = REBOOT;
				break;
			}
		
		} else if (bytesReceived <= 0){
			// Network error
			printf("\tERROR: Unrecognized network error code %d\n\r", 
				bytesReceived);
			returnCode = REBOOT;
			break;
		
		} else if (this->networkError){	
			// Network error
			printf("\tERROR: Network error flag raised\n\r");
			returnCode = REBOOT;
			break;
		
		} else {
			// Something was received. Reset timeout counter

			mosiBuffer[bytesReceived < bufferSize? bytesReceived:bufferSize-1] =
				'\0';
			timeouts = 0;

			// Parse message:

			/* NOTE: The following are expected broadcast formats:
			 * 
			 * FORMAT                                  | MEANING
			 * ----------------------------------------+----------------------------
			 * 00000000|password|N|listenerPort        | STD broadcast
			 * 00000000|password|S                     | Start application
			 * 00000000|password|U|filename            | HSK for update
			 * ----------------------------------------+----------------------------
			 */
			
			char *splitPointer = NULL, *savePointer = NULL;
			// Skip index and password:
			strtok_r(mosiBuffer, "|", &savePointer); // Should point to index
			splitPointer = strtok_r(NULL, "|", &savePointer); // Should point to
															  // password

			snprintf(this->passwordBuffer, 32, splitPointer);

			// Prepare standard reply:
			snprintf(misoBuffer, bufferSize, "00000000|%s|B|%s|%u",
				this->passwordBuffer, 
				this->ethernet->get_mac_address(),
				this->listenerPort);

			// Get specifying character:
			splitPointer = strtok_r(NULL, "|", &savePointer); // Should point to 
															  // spec. character

			// Check for errors:
			if(splitPointer == NULL){
				// Bad message
				printf("\tERROR: Bad message from broadcast (\"%s\") discarded\n\r",
					mosiBuffer);
				continue;
			
			} else if (splitPointer[0] == 'S'){
				// Start application
				returnCode = START;
				break;
			
			} else if (splitPointer[0] == 'N'){
				// Standard broadcast. Send standard reply
					
				// Fetch Master listener port (MISO port):
				splitPointer = strtok_r(NULL, "|", &savePointer);
				if(splitPointer == NULL){
					printf("\tERROR: NULL splitter when getting Master "\
						"listener port\n\r");
					continue;	
				}
				this->misoPort = atoi(splitPointer);
				if(this->misoPort <= 0 or this->misoPort >= 65535){
					printf("\tERROR: Bad Master listener port (\"%d\")\n\r",
						misoPort);
					continue;
				}

				// Send standard reply:
				this->listenerSocket.sendto(
					this->masterBroadcastAddress.get_ip_address(),
					this->misoPort,
					misoBuffer,
					strlen(misoBuffer)
				);

			} else if (splitPointer[0] == 'U') {
				// Fetch update
				
				// Get update port:
				splitPointer = strtok_r(NULL, "|", &savePointer);
				if(splitPointer == NULL){
					printf("\tERROR: NULL splitter when getting filename\n\r");
					continue;	
				}
				strcpy(this->filename, splitPointer);
				if(strlen(this->filename) <= 0){
					printf("\tERROR: Missing filename\n\r");
					continue;
				}
				
				returnCode = UPDATE;
				break;
			
			} else {
				// Unrecognized character. Discard message
				printf("\tERROR: Unrecognized character code '%c' discarded\n\r",
					splitPointer[0]);
				continue;
			}

				// To attempt a connection, send request and wait for reply
				// Either secure handshake or start application

		} // End check reception

	} while(timeouts <= this->maxRebootTimeouts);

	delete[] misoBuffer;
	delete[] mosiBuffer;

	return returnCode;

} // End listen

bool BTCommunicator::download(Callback<void(const char *at,size_t l)> cback,
	char errormsg[], int msgLength){

	// Try to get file ---------------------------------------------------------
	char address[128];


	/*
	NetworkInterface* network;
	network = easy_connect(true);

	if(network == NULL){
		printf("\tERROR: could not connect NetworkInterface\n\r");
		snprintf(errormsg, msgLength, "Could not connect NetworkInterface");
		return false; 
	}
	*/

	snprintf(address, 128, "http://%s:8000/%s",
		this->masterBroadcastAddress.get_ip_address(), this->filename);
	
	printf("\tConnecting to %s\n\r", address);
	
	HttpRequest* req = new HttpRequest(
		this->ethernet, HTTP_GET, address, cback);

	this->listenerSocket.close();

    HttpResponse* res = req->send();
    if (res == NULL) {
        snprintf(errormsg, msgLength,
			"HttpRequest failed (error code %d)", req->get_error());
        return false;
    }

	delete req;

	return true;

} // End download

int BTCommunicator::error(const char message[], int msgLength) {
	
	// Verify connection:
	if (misoPort == 0){
		// Also invalid MISO port
		printf("ERROR: BTC error called w/ MISO port 0 (disconnected?)\n\r");
		return 0;
	} // End verificaton

	char errorMessage[512];
	int i = 0;

	i = snprintf(errorMessage, 512, "00000000|%s|B|%s|BERR|",
		this->passwordBuffer,
		this->ethernet->get_mac_address()
	);

	snprintf(errorMessage + i, 
		msgLength < 512 - i ? msgLength : 512 - i - msgLength,
		message);

	// Send given error message:
	return this->listenerSocket.sendto(
		this->masterBroadcastAddress.get_ip_address(),
		this->misoPort,
		errorMessage,
		strlen(errorMessage)
	);

} // End error
