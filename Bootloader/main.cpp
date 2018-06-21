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

#define FCIIB_VERSION "INIT 0" // Initial version

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
#include "Serial.h"
#include "HeapBlockDevice.h"
#include "FATFileSystem.h"
#include "mbed.h"

//// SETTINGS //////////////////////////////////////////////////////////////////
#define BAUDRATE 460800
#define SOCKET_TIMEOUT_MS 1000
#define MAX_REBOOT_TIMEOUTS 30

#define LISTENER_PORT 65000
#define MISO_PORT 55000
#define MOSI_PORT 55001

#define UPDATE_HEAP_KBYTES 140
	// NOTE: The NUCLEO_F429ZI has about 250 KB's of RAM
#define UPDATE_BLOCKSIZE 512

#define FILENAME "/fs/update.bin"

#define MSG_LENGTH 128 // For message buffers

//// MAIN //////////////////////////////////////////////////////////////////////
int main() {

	// Initialization ==========================================================
	
	// Prepare Serial communications:
	Serial PC(USBTX, USBRX, BAUDRATE);

	// Print initialization message:
	printf(BTUtils::LN_LN_THICKLINE_LN);
	printf("FCMkII Bootloader (\"%s\") (%dKiB)\n\r", 
		FCIIB_VERSION, UPDATE_HEAP_KBYTES);
	printf(BTUtils::THINLINE_LN);
	
	// Store references to objects using hardware resources that need cleanup
	// (in order to safely launch application)
	#define numObjects 3
	int numAllocatedObjects = 0;
	void* objects[numObjects];
	for(int i = 0; i < numObjects; i++0){
		objects[i] = nullptr;
	}

	// TODO: Keep track of object sizes
	// TODO: Debug button

	printf("WARNING: SEE TODO'S IN SOURCE\n\r");

	// Initialize communications:
	BTCommunicator* comms = new BTCommunicator(
		SOCKET_TIMEOUT_MS, MAX_REBOOT_TIMEOUTS, LISTENER_PORT,
		MISO_PORT, MOSI_PORT);
	objects[numAllocatedObjects++] = comms;
	printf(BTUtils::THINLINE_LN);

	// Listen for messages:
	switch(comms->listen(MSG_LENGTH)){
		
		case START:
			// Launch FCMkII
			
			printf("Launching program\n\r");
			printf(THICKLINE_LN);
			
			// Clean up hardware: 
			// TODO: Cleanup
			printf("WARNING: NO HARDWARE CLEANUP\n\r");

			// Jump to MkII:
			BTUtils::launch(objects, numAllocatedObjects);
			break;
		
		case UPDATE:
			// Launch Update sequence
			printf("Processing update order\n\r");

			// Initialize filesystem -------------------------------------------
			printf("Setting up filesystem:\n\r");
	
			HeapBlockDevice bd(1024*UPDATE_HEAP_KBYTES, UPDATE_BLOCKSIZE);
			FATFileSystem fs("fs");

			if(bd.init != 0){
				printf("ERROR: could not initialize Heap Block Device\n\r");
				comms->error(
					"Filesystem error: could not initialize HeapBlockDevice");
				BTUtils::fatal();
			}

			if(FATFileSystem::format(&bd) == NULL){
				printf("ERROR: could not format filesystem\n\r");
				comms->error(
					"Filesystem error: could not format block device");
				BTUtils::fatal();
			}
			
			int errcode = -666;
			if((errcode = fs.mount(&bd)) != 0){
				printf("ERROR: could not mount filesystem (%d)\n\r", errcode);
				comms->error("Filesystem error: could not mount", errcode);
				BTUtils::fatal();
			}

			printf("\tFilesystem initialized w/ %dKiB and %dB blocks\n\r", 
				UPDATE_HEAP_KBYTES, UPDATE_BLOCKSIZE);

			// Download file ---------------------------------------------------
			char errormsg[MSG_LENGTH] = {0};
			FILE* file = fopen(FILENAME, "wb");
			comms->download(file, errormsg, MSG_LENGTH);
		
			if((errormsg[0] != '\0')){
				printf("ERROR downloading file: \"%s\"\n\r", 
					errormsg, MSG_LENGTH);
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

			if(errormsg[0] != '\0'){
				printf("Error flashing file: \"%s\"\n\r", errormsg, MSG_LENGTH);
				comms->error(errormsg, MSG_LENGTH);
				BTUtils::fatal();
			}

			// Jump to MkII ----------------------------------------------------
			BTUtils::launch(objects, numAllocatedObjects);

		case REBOOT:
			// Reboot Bootloader

			BTUtils::reboot();
	
	}
	

/* * SCRATCH:

	Need to:
	- UDP comms
		- Listen and respond to broadcast
		- Communicate w/ SV thread
		- 
	- Track comms status
	- HTTP transmission
	- Heap file management
	- Flash board w/ feedback for UDP
	

	OOP Breakdown:
	- BTCommunicator
	- BTDownloader
	- BTFlasher

	* Have Downloader and Flasher use externally declared file -> Set up file-
		system in main file.

* */

	// 

	return 0;
}

////////////////////////////////////////////////////////////////////////////////
