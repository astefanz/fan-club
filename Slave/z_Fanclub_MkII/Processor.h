////////////////////////////////////////////////////////////////////////////////
// Project: Fanclub Mark II "Slave" // File: Processor.h - Interface          //
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

#ifndef PROCESSOR_H
#define PROCESSOR_H

//// ABOUT /////////////////////////////////////////////////////////////////////
// This module handles control of fan hardware                                //
////////////////////////////////////////////////////////////////////////////////

//// DEPENDENCIES //////////////////////////////////////////////////////////////

#include "feedback.h"
#include "print.h"
#include "settings.h"

//// CONSTANT DECLARATIONS /////////////////////////////////////////////////////

extern const int  

    // STATUS CODES ------------------------------------------------------------
    BUSY,           // Active and fully configured, but busy w/ another command
    READY,          // Active, fully configured and ready to process commands
    UNCONFIGURED,   // Active but not configured. Only PWM out & default RPM in
    INACTIVE,       // Not active. Unable to process commands. Fans off.
    

    // FAN MODES ---------------------------------------------------------------
    SINGLE,
    DOUBLE;

extern const int GET_ERROR;

//// CLASS INTERFACE ///////////////////////////////////////////////////////////

class Processor { 

public:

    // CONSTRUCTORS AND DESTRUCTORS --------------------------------------------

    Processor(void);
        /* ABOUT: Constructor for class Processor. Starts processor thread.
         */
    
    // PUBLIC INTERFACE --------------------------------------------------------
    
    bool process(const char* command);
        /* ABOUT: Take a given command for processing.
         * PARAMETERS:
         * -const char* command: NULL-terminated string representing command to
         *  process.
         */
         
    void get(char* buffer);
        /* ABOUT: Get a reply to be sent to Master.
         * -PARAMETERS:
         * -const char* buffer: pointer to char array in which to store reply.
         */

    void setStatus(int status);
    	/* ABOUT: Modify Processor status.
    	 * PARAMETERS:
    	 * -int status: Integer code of new status to set. Must be defined in 
    	 * Processor.h.
    	 */

private:

    // INNER THREAD ROUTINES ---------------------------------------------------
    void _processorRoutine(void);
        /* ABOUT: To be executed by this Processor's processor thread.
         */
         
    void _blinkBlue(void);
        /* ABOUT: To be set as ISR for blue LED Ticker to show status.
         */
         
    Thread processorThread; // Executes _processorRoutine
    
    // PROFILE DATA ------------------------------------------------------------
    int8_t fanMode;         // Single or double fan configuration
    int targetRelation[2];  // (If applic.) Rel. between front and rear fan RPM
    uint8_t fanAmount;      // Number of active fans
    uint8_t counterCounts;  // Number of pulses to be counted when reading
    uint8_t pulsesPerRotation;   // Pulses sent by sensor in one full rotation
    uint8_t maxRPM;         // Maximum nominal RPM of fan model
    uint8_t minRPM;         // Minimum nominal nonzero RPM of fan model
    uint8_t minDC;          // Duty cycle corresponding to minRPM (nominal)
    
    // STATUS DATA -------------------------------------------------------------
    int8_t status;      // Current processor status
    DigitalOut blue;    // Access to blue LED
    Ticker blinker;     // Used to blink blue LED for status   
    Mutex arrayLock, taskLock, replyLock; // Thread safe access
    
    // PROCESS DATA ------------------------------------------------------------
    char taskBuffer[512];
    int rpms[MAX_FANS];
    float dcs[MAX_FANS];
    
};


#endif // PROCESSOR_H

