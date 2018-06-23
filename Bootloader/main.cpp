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

#define FCIIB_VERSION "1.0"

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
#define SOCKET_TIMEOUT_MS 500
#define MAX_REBOOT_TIMEOUTS 60*10*2 // (this*SOCKET_TIMEOUT_MS)/1000 seconds total

#define FLASH_BUFFER_SIZE 1024*1000 // Have 1,000 KB download buffer

#define LISTENER_PORT 65001

#define MAX_BYTES 32000 // For storage

#define FILENAME "/fs/a.bin"

#define BUFFER_SIZE 128
#define PW_BUFFER_SIZE 8
#define MAX_ADDRESS_SIZE 64

////////////////////////////////////////////////////////////////////////////////

// USAGE OF FLASH MEMORY:
/*

+----------------+ End of Flash: POST_APPLICATION_ADDR + POST_APPLICATION_SIZE 
|                |\
| FLASH BUFFER   | \__FLASH_BUFFER_SIZE
| (Download here)| /
|                |/
+----------------+
|                |
| MkII BINARY    |
| (Copy here)    |
|                |
+----------------+ End of Bootloader: APPLICATION_ADDR + APPLICATION_SIZE
| BOOTLOADER     |
+----------------+ Start of Bootloader: APPLICATION_ADDR
| Vector table   |
+================+

*/


//// CONSTANTS AND GLOBALS /////////////////////////////////////////////////////
enum BTCode {START, UPDATE, REBOOT};

uint32_t received;
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

	// Optional PSU pin:
	DigitalOut PSU_off(D9);
	PSU_off.write(true);

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
				printf("\n\r\tERROR: MAX TIMEOUTS\n\r");
				btCode = REBOOT;
				break;
			}
			continue;
			
		} else if (result <= 0){
			// Network error
			printf("\n\r\tERROR: CODE %d\n\r", 
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
				printf("\n\r\tERROR: BAD BCAST: \"%s\"\n\r",
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
					printf("\n\r\tERROR: NULL LISTN PORT\n\r");
					continue;	
				}
				misoPort = atoi(splitPointer);
				if(misoPort == 0){
					printf("\n\r\tERROR: 0 LISTN PORT\n\r");
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
					printf("\n\r\tERROR: NULL FILENAME\n\r");
					continue;	
				}
				strcpy(filename, splitPointer);
				if(strlen(filename) <= 0){
					printf("\n\r\tERROR: NO FILENAME\n\r");
					continue;
				}
				
				btCode = UPDATE;
				break;
			
			} else {
				// Unrecognized character. Discard message
				printf("\n\r\tERROR: BAD CODE '%c'\n\r",
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
			printf("\n\rUpdating\n\r");

			// Download file ---------------------------------------------------
			Ticker t;	
			
			t.attach(BTUtils::blinkMID, 0.2);
			
			char errormsg[BUFFER_SIZE] = {0};
			char address[MAX_ADDRESS_SIZE];
			snprintf(address, MAX_ADDRESS_SIZE, "http://%s:8000/%s",
				masterBroadcastAddress.get_ip_address(), filename);
			
			printf("\tConnecting to %s\n\r", address);
			
			BTFlash::flashIAP.init();
			HttpRequest* req = new HttpRequest(
				ethernet, HTTP_GET, address, _storeFragment);

			//listenerSocket.close();

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
			printf("\n\n\rDownload successful\n\n\r");

			// Flash file ------------------------------------------------------
			printf("Flashing file\n\r");	
			t.detach();
			t.attach(BTUtils::blinkMID, 0.1);

			BTFlash::copy(
				POST_APPLICATION_ADDR + POST_APPLICATION_SIZE - 
					FLASH_BUFFER_SIZE,
				received,
				POST_APPLICATION_ADDR);
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

			t.detach();
			BTFlash::flashIAP.deinit();

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

	static bool initialized = false;
    static bool sector_erased = false;
	static uint32_t addr = 
		POST_APPLICATION_ADDR + POST_APPLICATION_SIZE - FLASH_BUFFER_SIZE;
	static uint32_t addr_original = addr;
	static char* page_buffer;
	static uint32_t page_size;
	static uint32_t next_sector;
    static size_t pages_flashed = 0;
	
	if(not initialized){
		int res = BTFlash::flashIAP.init();
		page_size = BTFlash::flashIAP.get_page_size();
		page_buffer = new char[page_size];
    	next_sector = addr + BTFlash::flashIAP.get_sector_size(addr);
		initialized = true;
		printf("\tWriting directly to flash memory (%d)\n\r"\
			"\t\tSector size: %lu B\n\r\t\tPage size: %lu B\n\r", 
			res, BTFlash::flashIAP.get_sector_size(addr), page_size);
	}
	
	//printf("\tWriting %lu bytes starting on 0x%lx\n\r", size, addr);

    receivedPackets++;

	uint32_t target_addr = addr + size;
	uint16_t count = 0;
	while (addr < target_addr) {
		int result = -666;

		// Prevent overflows:
		if(addr == POST_APPLICATION_ADDR + POST_APPLICATION_SIZE){
			printf("ERROR: OUT OF SPACE\n\r");
			BTUtils::fatal();
		}

		// Get data to be written ..............................................

		// Wipe page_buffer:
		// Read data for this page
		memset(page_buffer, 0, sizeof(page_buffer));
        
		for(uint32_t i = 0; i < page_size; i++){
			page_buffer[i] = buffer[count + i];
			count++;
		}


        // Erase this page if it hasn't been erased
        if (!sector_erased) {
			printf("\n\n\r\tErasing sector on 0x%lx", addr);
			result = BTFlash::flashIAP.erase(addr, BTFlash::flashIAP.get_sector_size(addr));
        	if (result != 0){
				printf("(got %d)\n\r",result);
				// NOTE: error code occurs when erasing previously erased flash
				// (benign)
				// Error erasing
				//BTUtils::fatal();
			//	break;
			} else{
			
				printf("\n\r");
			}
			sector_erased = true;
        }
		

        // Program page
		result = BTFlash::flashIAP.program(page_buffer, addr, page_size);
		if (result != 0){
			// Error writing
			printf("\n\r\tError (%d) while writing on 0x%lx\n\r",
				result, addr);
			BTUtils::fatal();

			break;
		}
        

		addr += page_size;
		received += page_size;
        if (addr >= next_sector) {
            next_sector = addr + BTFlash::flashIAP.get_sector_size(addr);
            sector_erased = false;
        }

		pages_flashed++;
		
		/*
			printf("\r\tFlashed %lu page(s) (@0x%lx) (%d)", 
				pages_flashed, addr, sector_erased);
		*/

		if(received >= FLASH_BUFFER_SIZE){
			printf("ERROR: NOT ENOUGH ROOM\n\r");
			BTUtils::fatal();
		}
    }
	printf("\r\tDownloaded %lu B [0x%lx, 0x%lx]", 
		received, addr_original, addr);
	
	
	
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
