////////////////////////////////////////////////////////////////////////////////
// Project: Fanclub Mark II "Slave" // File: print.h - Global print function  //
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

#ifndef PRINT_H
#define PRINT_H

//// IMPORTS ///////////////////////////////////////////////////////////////////

#include "Mutex.h" // For thread-safety
#include "mbed.h" // For custom baud rates

#include "settings.h" // Custom settings

//// CONSTANTS & GLOBALS ///////////////////////////////////////////////////////

#define pl PL.lock();
#define pu PL.unlock();
#define tm T.read_ms()

#define sl SL.lock();
#define su SL.unlock();

extern const char* INIT;

extern Serial PC;

extern Mutex PL; // "Print lock" to share printf among threads
extern Mutex SL; // "Split lock" to share strtok among threads

extern Timer T; // For timestamps

#endif  // PRINT_H