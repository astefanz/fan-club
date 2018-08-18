////////////////////////////////////////////////////////////////////////////////
// Project: Fanclub Mark II "Slave" // File: settings.h - Global settings     //
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

#ifndef SETTINGS_H
#define SETTINGS_H


//#define JPL
//#define STACK_PRINTS
//#define HEAP_PRINTS

#if defined(STACK_PRINTS) || defined(HEAP_PRINTS)
#include "mbed_stats.h" // (For memory analysis)
#endif


//// ABOUT /////////////////////////////////////////////////////////////////////
// This file defines global settings (constant values) so  they  may  be  easily
// found and altered.
////////////////////////////////////////////////////////////////////////////////

//// GLOBAL CONSTANTS //////////////////////////////////////////////////////////

#define BAUD 921600// Serial baud rate
#define STACK_SIZE 4 // KB
#define NUMFANS 21  // Number of fans for pinout
#define BLINK_SLOW 0.5  // Long period of LED blinking (seconds) 
#define BLINK_FAST 0.1 // Short period of LED blinking (seconds)

// COMMUNICATIONS //////////////////////////////////////////////////////////////
#define BROADCAST_PORT 65000
#define TIMEOUT_MS 500
#define PASSCODE "CT"
#define SMISO 60000
#define SMOSI 60001
#define SLISTENER 65000
#define MAX_MESSAGE_LENGTH 512 // Characters
#define MAX_NETWORK_TIMEOUTS 10 // Before checking connection status
#define MAX_MASTER_TIMEOUTS 10 // Before assuming disconnection

// FAN ARRAY ///////////////////////////////////////////////////////////////////
#define MAX_FANS 21
#define DEFAULT_FAN_TIMEOUT_US 30000

#endif // SETTINGS_H
