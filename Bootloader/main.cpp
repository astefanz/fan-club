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
#include "HeapBlockDevice.h"
#include "FATFileSystem.h"
#include "mbed.h"

//// SETTINGS //////////////////////////////////////////////////////////////////
#define BAUDRATE 460800
#define SOCKET_TIMEOUT_MS 1000
#define MAX_REBOOT_TIMEOUTS 30

#define LISTENER_PORT 65000

#define UPDATE_HEAP_KBYTES 160
	// NOTE: The NUCLEO_F429ZI has about 250 KB's of RAM
#define UPDATE_BLOCKSIZE 512

#define FILENAME "/fs/a.bin"

#define MSG_LENGTH 256 // For message buffers

////////////////////////////////////////////////////////////////////////////////

FILE* file;
size_t received;
size_t receivedPackets;

void _storeFragment(const char* buffer, size_t size) {
  	int res = (int)fwrite(buffer, 1, size, file);

    received += size;
    receivedPackets++;

	if(receivedPackets %20 == 0)
		printf("\rDownloaded %uB [fwrite: %d]", received, res);

	/* (DEBUG)
    if (received_packets % 20 == 0) {
        printf("Received %u bytes\n", received);
    }
	*/
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

			// Initialize filesystem -------------------------------------------
			printf("Setting up filesystem:\n\r");
	
			HeapBlockDevice bd(1024*UPDATE_HEAP_KBYTES, UPDATE_BLOCKSIZE);
			FATFileSystem fs("fs");

			if(bd.init() != 0){
				printf("ERROR: could not initialize Heap Block Device\n\r");
				comms->error(
					"Filesystem error: could not initialize HeapBlockDevice",
					MSG_LENGTH	
				);
				BTUtils::fatal();
			}

			if(FATFileSystem::format(&bd) != 0){
				printf("ERROR: could not format filesystem\n\r");
				comms->error(
					"Filesystem error: could not format block device",
					MSG_LENGTH
				);
				BTUtils::fatal();
			}
			
			int errcode = -666;
			if((errcode = fs.mount(&bd)) != 0){
				printf("ERROR: could not mount filesystem (%d)\n\r", errcode);
				comms->error("Filesystem error: could not mount", MSG_LENGTH);
				BTUtils::fatal();
			}

			printf("\tFilesystem initialized w/ %dKiB and %dB blocks\n\r", 
				UPDATE_HEAP_KBYTES, UPDATE_BLOCKSIZE);

			// Download file ---------------------------------------------------
			char errormsg[MSG_LENGTH] = {0};
			file = fopen(FILENAME, "wb");
					
			if(!comms->download(_storeFragment, errormsg, MSG_LENGTH)){
				printf("ERROR downloading file: \"%s\"\n\r", 
					errormsg);
				comms->error(errormsg, MSG_LENGTH);
				BTUtils::fatal();
			}
			fclose(file);
			
			printf("File downloaded successfully\n\r");

			// Flash file ------------------------------------------------------
			printf("Flashing file\n\r");
			
			file = fopen(FILENAME, "rb");
			BTFlash::flash(file, POST_APPLICATION_ADDR, errormsg, MSG_LENGTH);
			fclose(file);

			printf("Done with BTFlash\n\r");

			if(errormsg[0] != '\0'){
				printf("Error flashing file: \"%s\"\n\r", errormsg);
				comms->error(errormsg, MSG_LENGTH);
				BTUtils::fatal();
			}

			// Disassemble filesystem ------------------------------------------
			printf("Disassembling Filesystem:\n\r");
			fs.unmount();
			bd.deinit();
			printf("\tDone\n\r");

			
			
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
