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

//// INCLUDES //////////////////////////////////////////////////////////////////
#include "BTCommunicator.h"

// FCMkII:
#include "BTDownloader.h"

// Mbed:
#include "EthernetInterface.h"
#include "UDPSocket.h"
#include "mbed.h"

// Standard:
#include <cstring.h>

//// FUNCTION DEFINITIONS //////////////////////////////////////////////////////

BTCommunicator::BTCommunicator(int socketTimeoutMS, int maxRebootTimeouts
	uint16_t listenerPort):
	ethernet(), listenerSocket(),
	masterBroadcastAddress(),
	listenerPort(listenerPort),
	misoPort(0),
	updatePort(0),
	socketTimeoutMS(socketTimeoutMS), maxRebootTimeouts(maxRebootTimeouts),
	networkError(false), endThread(false),
	downloader() {

	passwordBuffer[0] = '\0';

	int result = -666; // Keep track of error codes;

	// Initialize network ------------------------------------------------------

	// Ethernet interface:
	result = int(this->ethernet.connect());
	if (result != 0) {
		printf("\tERROR initializing ethernet interface (%d)", result);
		this->networkError = true;
		return;
	}

	// Sockets:
	
	this->listenerSocket.open(this->ethernet);
	this->listenerSocket.bind(listenerPort);
	this->listenerSocket.set_timeout(socketTimeoutMS);

	return;
} // End constructor

~BTCommunicator(void){
	
	// Close sockets and network interface:
	this->listenerSocket.close();
	this->misoSocket.close();
	this->mosiSocket.close();
	this->ethernet.disconnect();

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

			timeouts++;
			if (timeouts >= this->maxRebootTimeouts){
				printf("\tERROR: Timeout limit reached while listening");
				returnCode = REBOOT;
				break;
			}
		
		} else if (bytesReceived <= 0){
			// Network error
			printf("\tERROR: Unrecognized network error code %d", 
				bytesReceived);
			returnCode = REBOOT;
			break;
		
		} else if (this->networkError){	
			// Network error
			printf("\tERROR: Network error flag raised", 
				bytesReceived);
			returnCode = REBOOT;
			break;
		
		} else {
			// Something was received. Reset timeout counter

			timeouts = 0;
		}

		// Parse message:

		/* NOTE: The following are expected broadcast formats:
		 * 
		 * FORMAT                                  | MEANING
		 * ----------------------------------------+----------------------------
		 * 00000000|password|N|listenerPort        | STD broadcast
		 * 00000000|password|S                     | Start application
		 * 00000000|password|U|updatePort          | HSK for update
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
			this->ethernet.get_mac_address(),
			this->listenerPort);

		// Get specifying character:
		splitPointer = strtok_r(NULL, "|", &savePointer); // Should point to 
														  // spec. character

		// Check for errors:
		if(splitPointer == NULL){
			// Bad message
			printf("\tERROR: Bad message from broadcast (\"%s\") discarded",
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
				printf("\tERROR: NULL splitter when getting Master listener port");
				continue;	
			}
			this->misoPort = atoi(splitPointer);
			if(this->misoPort <= 0 or this->misoPort >= 65535){
				printf("\tERROR: Bad Master listener port (\"%d\")", misoPort);
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
				printf("\tERROR: NULL splitter when getting Master update port");
				continue;	
			}
			this->updatePort = atoi(splitPointer);
			if(this->updatePort <= 0 or this->updatePort >= 65535){
				printf("\tERROR: Bad Master update port (\"%d\")", updatePort);
				continue;
			}
			
			returnCode = UPDATE;
			break;
		
		} else {
			// Unrecognized character. Discard message
			printf("\tERROR: Unrecognized character code '%c' discarded",
				splitPointer[0]);
			continue;
		}

			// To attempt a connection, send request and wait for reply
			// Either secure handshake or start application
	
	} while(timeouts <= this->maxRebootTimeouts);

	delete[] misoBuffer;
	delete[] mosiBuffer;

	return returnCode;

} // End listen

bool BTCommunicator::download(FILE* file, char errormsg[], int msgLength){
	
	// Verify file -------------------------------------------------------------
	if (file == NULL){
		printf("\tERROR: NULL file pointer in download function\n\r");
		snprintf(errormsg, msgLength, "NULL file pointer in download function");
		return false;
	}

	// Verify connection -------------------------------------------------------
	if(this->misoPort < 0 or this->misoPort > 65535){
		// Invalid Master listener port. Cannot send error message
		printf("ERROR: BTC download called w/ invalid MISO port %d\n\r",
			misoPort);
		return 0;

	} else if (misoPort == 0){
		// Also invalid MISO port
		printf("ERROR: BTC download called w/ MISO port 0 (disconnected?)\n\r",
			misoPort);
		return 0;
	}

	// Download update ---------------------------------------------------------

	bool done = false;
	bool success = false;

	// Start download
	this->downloader.download(
		file, masterBroadcastAddress.get_ip_address(), misoPort,
		errormsg, msgLength);

	printf("\r\tDownloading [  0%%]");

	// Track download
	while (not done){
	
		// Check download status:
		DWStatus status = this->downloader.getStatus();

		switch(status){
		
			case DOWNLOADING:	
				printf("\r\tDownloading [%3u%%]", 
					this->downloader.getPercentage());
				break;

			case ERROR:
				// NOTE: Error message will be written by downloader
				printf("\n\tERROR in Downloader\n\t");
				success = false;
				done = true;
				break;

			case DONE:
				printf("\r\tDownloading [100%%]", 
				success = true;
				done = true;
				break;

			default:
				printf("\r\tERROR: unrecognized Downloader status code %d\n\t",
					int(status));
				this->downloader.shutdown();
				success = false;
				done = true;
				break;
		}

	} // End track download

	return success;

} // End download

int BTCommunicator::error(char message[], int msgLength) const {
	
	// Verify connection:
	if(this->misoPort < 0 or this->misoPort > 65535){
		// Invalid Master listener port. Cannot send error message
		printf("ERROR: BTC error called w/ invalid MISO port %d\n\r",
			misoPort);
		return 0;

	} else if (misoPort == 0){
		// Also invalid MISO port
		printf("ERROR: BTC error called w/ MISO port 0 (disconnected?)\n\r",
			misoPort);
		return 0;
	} // End verificaton

	char errorMessage[512];
	int i = 0;

	i = snprintf(errorMessage, 512, "00000000|%s|B|%s|BERR|",
		this->passwordBuffer,
		this->ethernet.get_mac_address(),
	);

	// TODO: WRITING SAFE PRINT INTO ERRORMSG BUFFER

	snprintf(errorMessage + i, i + msgLength < 512?

	// Send given error message:
	return this->listenerSocket.sendto(
		this->masterBroadcastAddress.get_ip_address(),
		this->misoPort,
		errorMessage,
		strlen(errorMessage)
	);

} // End error

