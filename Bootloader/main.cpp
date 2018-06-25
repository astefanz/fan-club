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

#define FCIIB_VERSION "S1.6"

////////////////////////////////////////////////////////////////////////////////
/* * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *
 * ABOUT: The FCMkII bootloader is meant to go along the FCMkII Slave binary  *
 * to allow for firmware updates over ethernet (to be sent by FCMkII Master)  *
 * NOTE: In order to minimize footprint, a few structural compromises were    *
 * made. Apologies to the fellow programmers who find the lack of encapsula-  *
 * tion repulsive.                                                            *
  * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * */
////////////////////////////////////////////////////////////////////////////////

//// INCLUDES //////////////////////////////////////////////////////////////////

// FCMkII:
#include "BTUtils.h" // Auxiliary functions and definitions
#include "BTFlash.h" // Write to flash memory

// Mbed:
#include "mbed.h"

// HTTP Client:
#include "http_request.h"
#include "EthernetInterface.h"
// SEE
// http://blog.janjongboom.com/2017/10/06/firmware-updates-flashiap.html
//	(For HTTP flashing)

// Standard:
#include <cstring>
#include <stdint.h>

//// SETTINGS //////////////////////////////////////////////////////////////////
// Network:
#define BAUDRATE 460800
#define SOCKET_TIMEOUT_MS 500
#define MAX_REBOOT_TIMEOUTS 60*10*2 // (this*SOCKET_TIMEOUT_MS)/1000 seconds total
#define LISTENER_PORT 65000

// Command specifiers:
#define STD_BCAST 'N'
#define UPDATE_COMMAND 'U'
#define SHUTDOWN_COMMAND 'R'
#define LAUNCH_COMMAND 'L'

// Storage:
#define FLASH_BUFFER_SIZE 1024*1000 // Have 1,000 KB download buffer
#define BUFFER_SIZE 128
#define PW_BUFFER_SIZE 8
#define MAX_ADDRESS_SIZE 64
#define FILENAME "/fs/a.bin"
#define MAX_FILENAME_LENGTH 16

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


// Network attributes:
NetworkInterface* ethernet;
UDPSocket listenerSocket;
SocketAddress masterBroadcastAddress;

// Network data:
uint16_t misoPort = 0;
char passcodeBuffer[PW_BUFFER_SIZE] = {0};
char misoBuffer[BUFFER_SIZE] = {0};
char mosiBuffer[BUFFER_SIZE] = {0};
char errorBuffer[BUFFER_SIZE] = {0};
uint32_t received = 0;
size_t receivedPackets = 0;
bool errorflag;
size_t receivedError = 0;
size_t printed = 0;

// Misc. tools:
Ticker ticker; // For LED blinking

//// FUNCTION PROTOTYPES ///////////////////////////////////////////////////////

// Storage ---------------------------------------------------------------------
void _storeFragment(const char buffer[], size_t size);

// Network ---------------------------------------------------------------------
void sendError(const char message[], size_t length);	

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
	printf("FCMkII Bootloader (\"%s\") (%d KB) (Port: %d)\n\r", 
		FCIIB_VERSION, FLASH_BUFFER_SIZE/1000, LISTENER_PORT);
	printf("----------------------------------------------------------------"\
		"----------------\n\r");
	
	// Initialize communications -----------------------------------------------
	printf("Init. Network:\n\r ");
	
	// Network interface and sockets:
	ethernet = new EthernetInterface;
	int c = ethernet->connect();
	if(c < 0){
		printf("\n\tETHERNET CONNECTION ERROR");
		BTUtils::fatal();
	}

	listenerSocket.open(ethernet);
	listenerSocket.bind(LISTENER_PORT);
	listenerSocket.set_timeout(SOCKET_TIMEOUT_MS);

	printf("\tConnected: %s (%d) MAC: %s\n\r", 
		ethernet->get_ip_address(), LISTENER_PORT, ethernet->get_mac_address());
	
	// Storage:
	char filename[MAX_FILENAME_LENGTH] = {0};
	char addressBuffer[MAX_ADDRESS_SIZE] = {0};
	uint32_t filesize = 0;

	// Networking:
	uint32_t timeouts = 0;

	// Listen for messages -----------------------------------------------------
	printf("Listening:\n\r");
	BTUtils::setLED(BTUtils::MID, BTUtils::ON);
	
	
	do { // ....................................................................
		
		// Reset values:
		misoPort = 0;
		for(uint8_t i = 0; i < BUFFER_SIZE; i++){
			misoBuffer[i] = '\0';
			mosiBuffer[i] = '\0';
			
			if(i < PW_BUFFER_SIZE){
				passcodeBuffer[i] = '\0';
			}
		}

		int result = -666;	

		// Listen for broadcast:
		result = listenerSocket.recvfrom(
			&masterBroadcastAddress, mosiBuffer, BUFFER_SIZE); 

		// Check for errors:
		if (result == NSAPI_ERROR_WOULD_BLOCK){
			// Timed out
			// Check network status
			
			nsapi_connection_status_t cstatus = 
				ethernet->get_connection_status();
			switch(cstatus){
				case NSAPI_STATUS_GLOBAL_UP:
					printf("\r\tWaiting [%10lu] (Connection: Global IP)",
						timeouts++);
					break;

				case NSAPI_STATUS_LOCAL_UP:
					printf("\r\tWaiting [%10lu] (Connection:  Local IP)",
						timeouts++);
					break;

				case NSAPI_STATUS_DISCONNECTED:
					printf("\n\rERROR: DISCONNECTED FROM NETWORK\n\r");
					BTUtils::fatal();
					break;

				default:
					printf("\n\rERROR: UNRECOGNIZED NETWORK STATUS CODE %d",
						cstatus);
			}
		

		} else if (result <= 0){
			// Network error
			printf("\n\r\tERROR: SOCKET ERR. CODE %d\n\r", 
				result);

			BTUtils::fatal();
			break;
		
		} else {
			// Something was received. Reset timeout counter
			printf("\n\rMessage received from %s", 
				masterBroadcastAddress.get_ip_address());

			// Add null-termination character
			mosiBuffer[result < BUFFER_SIZE? result:BUFFER_SIZE-1] = '\0';
			timeouts = 0;

			// Parse message:

			/* NOTE: The following are expected broadcast formats:
			 * 
			 * FORMAT                        | MEANING           | ACTION
			 * ------------------------------+-------------------+--------------
			 * N|PASSCODE|MLPORT             | STD broadcast     | Send reply*
			 * U|MLPORT|FNAME|FBYTES         | Update            | Contact HTTP
			 * R|PASSCODE                    | Shutdown (reboot) | Reboot
			 * L|PASSCODE                    | Start application | Launch MkII
			 * ------------------------------+-------------------+--------------
			 * *Reply format: B|passcode|MAC
			 */
			
			// Prepare placeholders for (potential) parsing:
			char *splitPointer = NULL, *savePointer = NULL;

			// Check message:
			switch(mosiBuffer[0]){
				
				case STD_BCAST: // Standard broadcast ..........................
					// Validate message and send reply
					printf("\n\rStandard broadcast received");

					// Get passcode
					strtok_r(mosiBuffer, "|", &savePointer); // Point to char.
					splitPointer = 
						strtok_r(NULL, "|", &savePointer); // Point to passcode
				
					if(splitPointer == NULL or splitPointer[0] == '\0'){
						// NOTE: Relying on short-circuiting here...
						printf("\n\r\tERROR: NULL PASSCODE");
						continue;
					}
					strcpy(passcodeBuffer, splitPointer);

					// Get Master Listener port
					splitPointer = 
						strtok_r(NULL, "|", &savePointer); // Point to MLPORT
				
					if(splitPointer == NULL or splitPointer[0] == '\0'){
						// NOTE: Relying on short-circuiting here...
						printf("\n\r\tERROR: NULL ML PORT");
						continue;
					} else if ((misoPort = atoi(splitPointer)) == 0){
						printf("\n\r\tERROR: ML PORT 0");
						continue;
					}

					
					// Format reply:
					snprintf(misoBuffer, BUFFER_SIZE,"B|%s|%s",
						passcodeBuffer, ethernet->get_mac_address());

					// Send reply:
					listenerSocket.sendto(
						masterBroadcastAddress.get_ip_address(),
						misoPort,
						misoBuffer,
						strlen(misoBuffer)
					);

					printf("\n\r\tReply sent: \"%s\"",
						misoBuffer);

					continue;
					break;

				case UPDATE_COMMAND: {// Update command ........................
					// Validate message and proceed to fetch update
					printf("\n\rUpdate order received");
					
					// Get passcode
					strtok_r(mosiBuffer, "|", &savePointer); // Point to char.
					splitPointer = 
						strtok_r(NULL, "|", &savePointer); // Point to passcode
				
					if(splitPointer == NULL or splitPointer[0] == '\0'){
						// NOTE: Relying on short-circuiting here...
						printf("\n\r\tERROR: NULL PASSCODE");
						continue;
					}
					strcpy(passcodeBuffer, splitPointer);


					// Get Master Listener Port
					splitPointer = 
						strtok_r(NULL, "|", &savePointer); // Point to MLPORT

					if(splitPointer == NULL or splitPointer[0] == '\0'){
						// NOTE: Relying on short-circuiting here...
						printf("\n\r\tERROR: NULL ML PORT");
						continue;
					} else if ((misoPort = atoi(splitPointer)) == 0){
						printf("\n\r\tERROR: ML PORT 0");
						continue;
					}

					// Get filename
					splitPointer = 
						strtok_r(NULL, "|", &savePointer); // Point to F.Name
					if(splitPointer == NULL){
						printf("\n\r\tERROR: NULL FILE NAME");
						sendError("NULL file name", 14);
						continue;
					} else if(strlen(splitPointer) > MAX_FILENAME_LENGTH){
						printf("\n\r\tERROR: FILE NAME TOO LONG (>%d)",
							MAX_FILENAME_LENGTH);
						snprintf(errorBuffer, BUFFER_SIZE, 
							"File name too long (%d)", 
							MAX_FILENAME_LENGTH);
						sendError(errorBuffer, strlen(errorBuffer));
						continue;	
					} else {
						strcpy(filename, splitPointer);
						printf("\n\r\tFile name: %s", filename);
					}
								
					// Get filesize
					splitPointer = 
						strtok_r(NULL, "|", &savePointer); // Point to MLPORT

					if(splitPointer == NULL or splitPointer[0] == '\0'){
						// NOTE: Relying on short-circuiting here...
						printf("\n\r\tERROR: NULL FILE SIZE");
						sendError("NULL file size", 14); 
						continue;
					} else if ((filesize = atoi(splitPointer)) == 0){
						printf("\n\r\tERROR: FILE SIZE 0");
						sendError("File size 0", 11); 
						continue;
					} else {
						printf("\n\r\tFile size: %lu B", filesize);
					}

					// Proceed to update ---------------------------------------
					// Launch Update sequence
					printf("\n\rUpdating\n\r");

					// Download file -------------------------------------------
					ticker.attach(BTUtils::blinkMID, 0.2);
					
					snprintf(addressBuffer, MAX_ADDRESS_SIZE, 
						"http://%s:8000/%s",
						masterBroadcastAddress.get_ip_address(), filename);
					
					printf("\n\r\tConnecting to %s", addressBuffer);
					
					BTFlash::flashIAP.init();
					HttpRequest* req = new HttpRequest(
						ethernet, HTTP_GET, addressBuffer, _storeFragment);

					HttpResponse* res = req->send();
					if (res == NULL) {
						printf("\n\r\tERROR IN DOWNLOAD: %d", 
							req->get_error());
						snprintf(errorBuffer, BUFFER_SIZE,
							"Download error (%d)", req->get_error());
						sendError(errorBuffer, strlen(errorBuffer));
						BTUtils::fatal();
					} else if (received != filesize){
						printf("\n\r\tERROR: FILE SIZE MISMATCH:"\
							"COUNTED %lu B, EXPECTED %lu B",
							received, filesize);
						snprintf(errorBuffer, BUFFER_SIZE,
							"File size mismatch: %lu B, exp't %lu B",
							received, filesize);
						sendError(errorBuffer, strlen(errorBuffer));
						
						// RIP
						BTUtils::fatal();
					}
					delete req;
					printf("\n\rDownload successful");

					// Flash file ----------------------------------------------
					printf("\n\rFlashing file");
					ticker.detach();
					ticker.attach(BTUtils::blinkMID, 0.1);

					BTFlash::copy(
						POST_APPLICATION_ADDR + POST_APPLICATION_SIZE - 
							FLASH_BUFFER_SIZE,
						received,
						POST_APPLICATION_ADDR,
						errorBuffer,
						BUFFER_SIZE);
					printf("\n\rDone flashing");

					if(errorBuffer[0] != '\0'){
						printf("\n\rERROR IN FLASHING: %s", errorBuffer);
						sendError(errorBuffer, strlen(errorBuffer));
						BTUtils::fatal();
					}

					ticker.detach();
					BTFlash::flashIAP.deinit();

					// Jump to MkII --------------------------------------------
					BTUtils::launch();
					break;
				} // End case UPDATE_COMMAND

				case LAUNCH_COMMAND: // Launch application (MkII) ..............
					// Launch MkII

					// Check for nonempty passcode:	
					strtok_r(mosiBuffer, "|", &savePointer); // Point to char.
					splitPointer = 
						strtok_r(NULL, "|", &savePointer); // Point to passcode
					
					if(strlen(splitPointer) > 0){
						// Nonempty passcode. Proceed to reboot
						printf("\n\rLaunch order received ");
						// Jump to MkII:
						BTUtils::launch();
						break;

					} else {
						// Invalid message
						printf("\n\rERROR: NO PASSCODE IN \"%s\"", 
							splitPointer);
						continue;
					}
					break;

				case SHUTDOWN_COMMAND: // Shutdown MCU .........................
					// Reboot
					
					// Check for nonempty passcode:					
					strtok_r(mosiBuffer, "|", &savePointer); // Point to char.
					splitPointer = 
						strtok_r(NULL, "|", &savePointer); // Point to passcode
				
					if(strlen(splitPointer) > 0){
						// Nonempty passcode. Proceed to reboot
						printf("\n\rShutdown order received");
						BTUtils::reboot();
					} else {
						// Invalid message
						printf("\n\rERROR: NO PASSCODE IN \"%s\"", 
							splitPointer);
						continue;
					}
					break;

				default: // Unrecognized command specifier .....................
					// Print error message
					printf("\n\rERROR. BAD CHAR CODE: '%c'",
						mosiBuffer[0]);
					// Try to send error message (listener port might not be
					// recorded)
					snprintf(errorBuffer, BUFFER_SIZE,
						"Bad char. code: %c", mosiBuffer[0]);
					sendError(errorBuffer, strlen(errorBuffer));
					BTUtils::fatal();
					break;

			} // End switch
		
		} // End message reception test

	} while(timeouts <= MAX_REBOOT_TIMEOUTS);

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
		printf("\n\r\tWriting directly to flash memory (%d)\n\r"\
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
			printed  = snprintf(errorBuffer, BUFFER_SIZE,
				"Error code %d while writing on 0x%lx", 
				result, addr);
			sendError(errorBuffer, printed);
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
			printf("\n\r\tERROR: NOT ENOUGH ROOM (%lu B/ %d B)",
				received, FLASH_BUFFER_SIZE);
			printed  = snprintf(errorBuffer, BUFFER_SIZE,
				"Flash buffer exhausted: %lu B / %d B", 
				received, FLASH_BUFFER_SIZE);
			sendError(errorBuffer, printed);
			BTUtils::fatal();
		}
    }
	printf("\r\tDownloaded %lu B [0x%lx, 0x%lx]", 
		received, addr_original, addr);
	
	
	
} // End _storeFragment

// Network ---------------------------------------------------------------------
void sendError(const char message[], size_t length){	
	
	static char errorMessage[BUFFER_SIZE];
	int sent;
	
	if(misoPort == 0){
		printf("\n\rERROR: Tried to send error message \"%s\" w/o MISO port",
			message);
	}

	// Format error message
	snprintf(errorMessage, BUFFER_SIZE, "B|%s|E|%s|%s",
		passcodeBuffer,
		ethernet->get_mac_address(),
		message
	);
	
	// Send given error message:
	if( (sent = listenerSocket.sendto(
			masterBroadcastAddress.get_ip_address(),
			misoPort, 
			errorMessage,
			strlen(errorMessage))) <= 0 ){

		printf("FAILED TO SEND ERROR MESSAGE: %d\n\r", sent);
	}

	return;

} // End sendError
