////////////////////////////////////////////////////////////////////////////////
// Project: Fanclub Mark II "Bootloader" // File: main.cpp - Main file        //
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

#define FCIIB_VERSION "ARRAY SLIM 1" // Initial version

////////////////////////////////////////////////////////////////////////////////
/* * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *
 * ABOUT: The FCMkII bootloader is meant to go along the FCMkII Slave binary  *
 * to allow for firmware updates over ethernet (to be sent by FCMkII Master)  *
 *                                                                            *
  * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * */
////////////////////////////////////////////////////////////////////////////////

//// INCLUDES //////////////////////////////////////////////////////////////////

// FCMkII:
#include "BTUtils.h" // Auxiliary functions and definitions
#include "BTFlash.h" // Write to flash memory

// Mbed:
#include "mbed.h"

// HTTP Client:
#include "easy-connect.h"
#include "http_request.h"
// SEE
// http://blog.janjongboom.com/2017/10/06/firmware-updates-flashiap.html
//	(For HTTP flashing)

// Standard:
#include <cstring>
#include <stdint.h>

//// SETTINGS //////////////////////////////////////////////////////////////////
#define BAUDRATE 460800
#define SOCKET_TIMEOUT_MS 1000
#define MAX_REBOOT_TIMEOUTS 30

#define LISTENER_PORT 65001

#define MAX_BYTES 72000 // For storage

#define FILENAME "/fs/a.bin"

#define BUFFER_SIZE 128
#define PW_BUFFER_SIZE 8
#define MAX_ADDRESS_SIZE 64

////////////////////////////////////////////////////////////////////////////////

//// CONSTANTS AND GLOBALS /////////////////////////////////////////////////////
enum BTCode {START, UPDATE, REBOOT};

size_t received;
size_t receivedPackets;
bool errorflag;
size_t receivedError = 0;
int errorBuffer[4] = {0};
char storage[MAX_BYTES] = {0};


//// FUNCTION PROTOTYPES ///////////////////////////////////////////////////////

// Storage ---------------------------------------------------------------------
void _storeFragment(const char buffer[], size_t size);

// Network ---------------------------------------------------------------------
void sendError(const char message[], size_t length, UDPSocket& socket, 
	const char ip[], const uint16_t port, const char password[], 
	const char mac[]);	

//// MAIN //////////////////////////////////////////////////////////////////////
int main() {

	// Initialization ==========================================================

	BTUtils::setLED(BTUtils::RED, BTUtils::ON);

	// Prepare Serial communications:
	Serial PC(USBTX, USBRX, BAUDRATE);

	// Print initialization message:
	printf("\n\n\r==========================================================="\
	"=====================\n\r");
	printf("FCMkII Bootloader (\"%s\") (%d B) (Port: %d)\n\r", 
		FCIIB_VERSION, MAX_BYTES, LISTENER_PORT);
	printf("----------------------------------------------------------------"\
		"----------------\n\r");
	
	// Initialize communications -----------------------------------------------
	printf("Init. Network:\n\r ");
	
	// Network attributes:
	NetworkInterface* ethernet;
	UDPSocket listenerSocket;
	SocketAddress masterBroadcastAddress;
	uint16_t misoPort = 0;
	char passwordBuffer[PW_BUFFER_SIZE] = {0};
	char misoBuffer[BUFFER_SIZE] = {0};
	char mosiBuffer[BUFFER_SIZE] = {0};

	// Network interface and sockets:
	ethernet = easy_connect(false);	
	if(ethernet == NULL){
		printf("\n\tETH ERROR");
		BTUtils::fatal();
	}

	listenerSocket.open(ethernet);
	listenerSocket.bind(LISTENER_PORT);
	listenerSocket.set_timeout(SOCKET_TIMEOUT_MS);

	printf("\tConnected: %s (%d)\n\r", 
		ethernet->get_ip_address(), LISTENER_PORT);
	
	// Storage:
	char filename[8] = {0};

	// Listen for messages -----------------------------------------------------
	printf("Listening:\n\r");
	BTUtils::setLED(BTUtils::MID, BTUtils::ON);

	BTCode btCode = REBOOT;
	int timeouts = 0;
	
	do { // ....................................................................
		
		// Reset values:
		misoPort = 0;
		for(uint8_t i = 0; i < BUFFER_SIZE; i++){
			misoBuffer[i] = '\0';
			mosiBuffer[i] = '\0';
			
			if(i < PW_BUFFER_SIZE){
				passwordBuffer[i] = '\0';
			}
		}

		int result = -666;	
		
		// Listen for broadcast:
		result = listenerSocket.recvfrom(
			&masterBroadcastAddress, mosiBuffer, BUFFER_SIZE); 

		// Check for errors:
		if (result == NSAPI_ERROR_WOULD_BLOCK){
			// Timed out
			printf("\tWaiting... [%2d/%2d]\n\r", 
				timeouts, MAX_REBOOT_TIMEOUTS);

			timeouts++;
			if (timeouts >= MAX_REBOOT_TIMEOUTS){
				printf("\tERROR: MAX TIMEOUTS\n\r");
				btCode = REBOOT;
				break;
			}
		
		} else if (result <= 0){
			// Network error
			printf("\tERROR: CODE %d\n\r", 
				result);
			btCode = REBOOT;
			break;
		
		} else {
			// Something was received. Reset timeout counter

			// Add null-termination character
			mosiBuffer[result < BUFFER_SIZE? result:BUFFER_SIZE-1] = '\0';
			timeouts = 0;

			// Parse message:

			/* NOTE: The following are expected broadcast formats:
			 * 
			 * FORMAT                                  | MEANING
			 * ----------------------------------------+------------------------
			 * 00000000|password|N|listenerPort        | STD broadcast
			 * 00000000|password|S                     | Start application
			 * 00000000|password|U|filename            | HSK for update
			 * ----------------------------------------+------------------------
			 */
			
			char *splitPointer = NULL, *savePointer = NULL;
			// Skip index and password:
			strtok_r(mosiBuffer, "|", &savePointer); // Should point to index
			splitPointer = strtok_r(NULL, "|", &savePointer); // Should point to
															  // password

			// Save password
			snprintf(passwordBuffer, PW_BUFFER_SIZE, splitPointer);

			// Prepare standard reply:
			snprintf(misoBuffer, BUFFER_SIZE, "0|%s|B|%s|%u",
				passwordBuffer, 
				ethernet->get_mac_address(),
				LISTENER_PORT);

			// Get specifying character:
			splitPointer = strtok_r(NULL, "|", &savePointer); // Should point to 
															  // spec. character
			// Check for errors:
			if(splitPointer == NULL){
				// Bad message
				printf("\tERROR: BAD BCAST: \"%s\"\n\r",
					mosiBuffer);
				continue;
			
			} else if (splitPointer[0] == 'S'){
				// Start application
				btCode = START;
				break;
			
			} else if (splitPointer[0] == 'N'){
				// Standard broadcast. Send standard reply
					
				// Fetch Master listener port (MISO port):
				splitPointer = strtok_r(NULL, "|", &savePointer);
				if(splitPointer == NULL){
					printf("\tERROR: NULL LISTN PORT\n\r");
					continue;	
				}
				misoPort = atoi(splitPointer);
				if(misoPort == 0){
					printf("\tERROR: 0 LISTN PORT");
					continue;
				}

				// Send standard reply:
				listenerSocket.sendto(
					masterBroadcastAddress.get_ip_address(),
					misoPort,
					misoBuffer,
					strlen(misoBuffer)
				);

			} else if (splitPointer[0] == 'U') {
				// Fetch update
				
				// Get update port:
				splitPointer = strtok_r(NULL, "|", &savePointer);
				if(splitPointer == NULL){
					printf("\tERROR: NULL FILENAME\n\r");
					continue;	
				}
				strcpy(filename, splitPointer);
				if(strlen(filename) <= 0){
					printf("\tERROR: NO FILENAME\n\r");
					continue;
				}
				
				btCode = UPDATE;
				break;
			
			} else {
				// Unrecognized character. Discard message
				printf("\tERROR: BAD CODE '%c'\n\r",
					splitPointer[0]);
				continue;
			}

				// To attempt a connection, send request and wait for reply
				// Either secure handshake or start application

		} // End check reception

	} while(timeouts <= MAX_REBOOT_TIMEOUTS);


	// Process command ---------------------------------------------------------
	switch(btCode){
		
		case START: {
			// Launch FCMkII

			// Jump to MkII:
			BTUtils::launch();
			break;
		}
		case UPDATE: {
			// Launch Update sequence
			printf("Updating\n\r");

			// Download file ---------------------------------------------------
			char errormsg[BUFFER_SIZE] = {0};
			char address[MAX_ADDRESS_SIZE];
			snprintf(address, MAX_ADDRESS_SIZE, "http://%s:8000/%s",
				masterBroadcastAddress.get_ip_address(), filename);
			
			printf("\tConnecting to %s\n\r", address);
			
			HttpRequest* req = new HttpRequest(
				ethernet, HTTP_GET, address, _storeFragment);

			listenerSocket.close();

			HttpResponse* res = req->send();
			if (res == NULL) {
				printf("\n\rERROR IN DOWNLOAD: %d\n\r", 
					req->get_error());
				
				sendError("Download failed", 16, 
					listenerSocket, 
					masterBroadcastAddress.get_ip_address(), 
					misoPort, passwordBuffer, 
					ethernet->get_mac_address());

				delete req;
				BTUtils::fatal();
			}

			delete req;
			printf("\n\rDownload successful\n\r");

			// Flash file ------------------------------------------------------
			printf("Flashing file\n\r");	
			BTFlash::flash(storage, received, POST_APPLICATION_ADDR);
			printf("Done flashing\n\r");

			if(errormsg[0] != '\0'){
				printf("ERROR IN FLASHING\n\r");
				sendError("Flash failed", 16, 
					listenerSocket, 
					masterBroadcastAddress.get_ip_address(), 
					misoPort, passwordBuffer, 
					ethernet->get_mac_address());

				BTUtils::fatal();
			}
			
			// Jump to MkII ----------------------------------------------------
			BTUtils::launch();
			break;
		
		}
		case REBOOT: {
			// Reboot Bootloader
			
			BTUtils::reboot();
			break;
		}
		default: {
			printf("ERROR: BAD BTCode\n\r");
			BTUtils::fatal();
			break;
		}
	} // End switch

	return 0;

} // end main


////////////////////////////////////////////////////////////////////////////////

//// FUNCTION DEFINITIONS //////////////////////////////////////////////////////

// Storage ---------------------------------------------------------------------
void _storeFragment(const char buffer[], size_t size) {

    receivedPackets++;

	for(uint32_t i = 0; i < size; i++){
		storage[received++] = buffer[i];
	}

	if(receivedPackets %20 == 0){
		printf("\rDownloaded %u B", received);
	}

} // End _storeFragment

// Network ---------------------------------------------------------------------
void sendError(const char message[], size_t length, UDPSocket& socket, 
	const char ip[], const uint16_t port, const char password[], 
	const char mac[]){	
	
	static char errorMessage[BUFFER_SIZE];
	int sent;
	
	// Format error message
	snprintf(errorMessage, BUFFER_SIZE, "0|%s|B|%s|BERR|%s",
		password,
		mac,
		message
	);
	
	// Send given error message:
	if( (sent = socket.sendto(ip, port, errorMessage, strlen(errorMessage))) <= 0 ){
		printf("FAILED TO SEND ERROR MESSAGE: %d\n\r", sent);
	}

	return;

} // End sendError
