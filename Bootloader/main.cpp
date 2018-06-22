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

#define FCIIB_VERSION "INIT 1" // Initial version

////////////////////////////////////////////////////////////////////////////////
/* * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *
 * ABOUT: The FCMkII bootloader is meant to go along the FCMkII Slave binary  *
 * to allow for firmware updates over ethernet (to be sent by FCMkII Master)  *
 *                                                                            *
  * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * */
////////////////////////////////////////////////////////////////////////////////

//// INCLUDES //////////////////////////////////////////////////////////////////

// FCMkII:
#include "BTCommunicator.h" // Communicate w/ Master
#include "BTUtils.h" // Auxiliary functions and definitions
#include "BTFlash.h" // Write to flash memory

// Mbed:
#include "mbed.h"

//// SETTINGS //////////////////////////////////////////////////////////////////
#define BAUDRATE 460800
#define SOCKET_TIMEOUT_MS 1000
#define MAX_REBOOT_TIMEOUTS 30

#define LISTENER_PORT 65000

#define UPDATE_HEAP_KBYTES 76
	// NOTE: The NUCLEO_F429ZI has about 250 KB's of RAM
#define UPDATE_BLOCKSIZE 512

#define FILENAME "/fs/a.bin"

#define MSG_LENGTH 128 // For message buffers

////////////////////////////////////////////////////////////////////////////////

size_t received;
size_t receivedPackets;
bool errorflag;
size_t receivedError = 0;
int errorBuffer[4] = {0};

char storage[160000] = {0};

void _storeFragment(const char* buffer, size_t size) {

    receivedPackets++;

	for(uint32_t i = 0; i < size; i++){
		storage[received++] = buffer[i];
	}

	if(receivedPackets %20 == 0){
		printf("\rDownloaded %u B", received);
	}

} // End _storeFragment

//// MAIN //////////////////////////////////////////////////////////////////////
int main() {

	// Initialization ==========================================================

	BTUtils::setLED(BTUtils::RED, BTUtils::ON);

	// Prepare Serial communications:
	Serial PC(USBTX, USBRX, BAUDRATE);

	// Print initialization message:
	printf("\n\n\r==========================================================="\
	"=====================\n\r");
	printf("FCMkII Bootloader (\"%s\") (Capacity: %dKiB) (Port: %d)\n\r", 
		FCIIB_VERSION, UPDATE_HEAP_KBYTES, LISTENER_PORT);
	printf("----------------------------------------------------------------"\
		"----------------\n\r");
	
	// Initialize communications:
	printf("Starting communications:\n\r ");
	BTCommunicator* comms = new BTCommunicator(
		SOCKET_TIMEOUT_MS, MAX_REBOOT_TIMEOUTS, LISTENER_PORT);
	printf("\tDone\n\r");

	BTUtils::setLED(BTUtils::MID, BTUtils::ON);

	printf("Listening for messages:\n\r");
	// Listen for messages:
	switch(comms->listen(MSG_LENGTH)){
		
		case START: {
			// Launch FCMkII
			
			printf("Launching program\n\r");
			printf("--------------------------------------------------------"\
			"------------------------\n\n");

			// Jump to MkII:
			delete comms;
			mbed_start_application(POST_APPLICATION_ADDR);
			break;
		}
		case UPDATE: {
			// Launch Update sequence
			printf("Processing update order\n\r");

			// Download file ---------------------------------------------------
			char errormsg[MSG_LENGTH] = {0};
					
			if(!comms->download(_storeFragment, errormsg, MSG_LENGTH)){
				printf("\n\rERROR downloading file: \"%s\"\n\r", 
					errormsg);
				comms->error(errormsg, MSG_LENGTH);
				BTUtils::fatal();
			} else if (errorflag){
				printf("\n\rERROR: Write file error flag raised (byte %u)\n\r",
					receivedError);
				BTUtils::fatal();
			}
		
			printf("File downloaded successfully\n\r");

			// Flash file ------------------------------------------------------
			printf("Flashing file\n\r");
			
			BTFlash::flash(storage, received, POST_APPLICATION_ADDR);

			printf("Done with BTFlash\n\r");

			if(errormsg[0] != '\0'){
				printf("Error flashing file: \"%s\"\n\r", errormsg);
				comms->error(errormsg, MSG_LENGTH);
				BTUtils::fatal();
			}
			
			// Jump to MkII ----------------------------------------------------
			delete comms;
			printf("Launching application\n\r");
			mbed_start_application(POST_APPLICATION_ADDR);
			break;
		
		}
		case REBOOT: {
			// Reboot Bootloader
			
			printf("Rebooting\n\r");
			BTUtils::reboot();
			break;
		}
		default: {
			printf("ERROR: Unrecognized status code\n\r");
			BTUtils::fatal();
			break;
		}
	} // End switch

	return 0;

} // end main


////////////////////////////////////////////////////////////////////////////////
