////////////////////////////////////////////////////////////////////////////////
// Project: Fanclub Mark II "Slave" // File: leds.h - Implementation          //
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
// Alejandro A. Stefan Zavala // <alestefanz@hotmail.com> //                  //
////////////////////////////////////////////////////////////////////////////////

//// ABOUT /////////////////////////////////////////////////////////////////////
// This is a provisional LED control file.
////////////////////////////////////////////////////////////////////////////////

//// DEPENDENCIES //////////////////////////////////////////////////////////////

#include "leds.h"

//// CONSTANTS /////////////////////////////////////////////////////////////////

DigitalOut
            redLed(LED3), 
            blueLed(LED2), 
            greenLed(LED3);  
              

// LED CONTROL FUNCTION --------------------------------------------------------

// AUXILIARY FUNCTIONS ---------------------------------------------------------

void blinkRed(void){

    redLed = !redLed;        
    
}// end blinkRed

void blinkBlue(void){

    blueLed = !blueLed;        
    
}// end blinkRed

void blinkGreen(void){

    greenLed = !greenLed;        
    
}// end blinkRed
