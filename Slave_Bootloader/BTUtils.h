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
#include "mbed.h" // NVIC_SystemReset


////////////////////////////////////////////////////////////////////////////////
namespace BTUtils{

//// GLOBAL ACCESS /////////////////////////////////////////////////////////////

enum LedCode {RED = 0, MID, /*GREEN,*/ ALL};
// NOTE: GREEN (D5, i.e. PE_11) conflicts w/ JPL pinout
enum LedValue {ON, OFF, TOGGLE};

// LED's:

DigitalOut leds[2][2] = 
	{{DigitalOut(LED3), DigitalOut(LED2)/*, DigitalOut(LED3)*/},
	 {DigitalOut(PE_13), DigitalOut(PF_14)/*, DigitalOut(D5)*/}};


//// AUXILIARY FUNCTIONS ///////////////////////////////////////////////////////

/* Reboot MCU
 */
void reboot(void){
	printf("\n\rREBOOTING\n\r");
	wait(0.001);
	NVIC_SystemReset();
} // End reboot

/* Control LED's
 */
void setLED(LedCode led = ALL, LedValue value = TOGGLE){
	
	if(led == ALL){
		for(int i = 0; i < 2; i++){
			leds[0][i] = value == TOGGLE? !leds[0][i] : value == ON;
			leds[1][i] = leds[0][i];
		}
	} else {
		
		leds[0][led] = value == TOGGLE? !leds[0][led] : value == ON;
		leds[1][led] = leds[0][led];
	
	} return;

} // End setLED

void blinkMID(void){

	leds[0][MID] = !leds[0][MID];
	leds[1][MID] = leds[0][MID];

} // End blinkMID

/* Notify the user of a critical error and reboot.
 */
void fatal(void){
	printf("\n\rFATAL ERROR\n\r");
	
	// Blink LED's:
	for(int i = 0; i < 5; i++){
		setLED(RED, TOGGLE);
		wait(0.050);
	}
	
	reboot();
		// NOTE: reboot also in BTUtils

	return;
} // End fatal

void launch(void){

	setLED(ALL, OFF);
	printf("\n\rLaunching application\n\r");
	printf("==========================================================="\
		"=====================\n\r");
	wait(0.001);
	mbed_start_application(POST_APPLICATION_ADDR);
	// Launch application

} // End launch

} // End namespace BTUtils

#endif // BTUTILS_H
