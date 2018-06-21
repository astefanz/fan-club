////////////////////////////////////////////////////////////////////////////////
// Project: Fanclub Mark II "Bootloader" // File: BTUtils.h                   //
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

// ABOUT: Repository of auxiliary functions and definitions for FCMkIIB

#ifndef BTUTILS_H
#define BTUTILS_H

//// INCLUDES //////////////////////////////////////////////////////////////////

// Mbed:
#include "core_cm4.h" // NVIC_SystemReset


////////////////////////////////////////////////////////////////////////////////
namespace BTUtils{

//// CONSTANTS /////////////////////////////////////////////////////////////////

// Formatting:
const char THINLINE[] = 
"-------------------------------------------------------------------------------"
"-";

const char THICKLINE[] = 
"==============================================================================="
"=";

const char THINLINE_LN[] = 
"-------------------------------------------------------------------------------"
"-\n\r";

const char THICKLINE_LN[] = 
"==============================================================================="
"=\n\r";

const char LN_LN_THINLINE_LN[] = 
"\n\n"
"-------------------------------------------------------------------------------"
"-\n\r";

const char LN_LN_THICKLINE_LN[] = 
"\n\n"
"==============================================================================="
"=\n\r";

//// AUXILIARY FUNCTIONS ///////////////////////////////////////////////////////

/* Launch application. Deallocates objects for cleanup.
 */
void launch(void** toCleanUp, int amount){
	
	cleanup(toCleanUp, amount);
		// NOTE: deallocate also in BTUtils

	printf("Launching application\n\r");
	mbed_start_application(POST_APPLICATION_ADDR);

} // End launch

/* Clean up objects that use hardware resources by calling their destructors.
 * (Each of these is to clean itself up within its destructor.)
 */
void cleanup(void** toCleanUp, int amount){

	for(int i = 0; i < amount; i++){
		delete toCleanUp[i];
	}

	return;

} // End cleanup

/* Notify the user of a critical error and reboot.
 */
void fatal(void){
	prinf("[ERROR] FATAL BOOTLOADER ERROR. REBOOTING.\n\r");
	reboot();
		// NOTE: reboot also in BTUtils

	return;
} // End fatal

/* Reboot MCU
 */
void reboot(void){
	NVIC_SystemReset();
} // End reboot

} // End namespace BTUtils

#endif // BTUTILS_H
