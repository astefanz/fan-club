////////////////////////////////////////////////////////////////////////////////
// Project: Fanclub Mark II "Slave" // File: Processor.cpp - Implementation   //
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
// See Processor.h                                                            //
////////////////////////////////////////////////////////////////////////////////

#include "Processor.h"

//// CONSTANT DEFINITIONS //////////////////////////////////////////////////////

const int  

    // STATUS CODES ------------------------------------------------------------
    BUSY = 2,
    READY = 1,
    UNCONFIGURED = 0,
    INACTIVE = -1,
    

    // FAN MODES ---------------------------------------------------------------
    SINGLE = 1,
    DOUBLE = 2;

const int GET_ERROR = -2147483648;

//// CLASS IMPLEMENTATION //////////////////////////////////////////////////////

// CONSTRUCTORS AND DESTRUCTORS --------------------------------------------

Processor::Processor(void):blue(LED2){
    /* ABOUT: Constructor for class Processor. Starts processor thread.
     */

	// NOT IMPLEMENTED
}

// PUBLIC INTERFACE --------------------------------------------------------

bool Processor::process(const char* command){
    /* ABOUT: Take a given command for processing.
     * PARAMETERS:
     * -const char* command: NULL-terminated string representing command to
     *  process.
     */

	// NOT IMPLEMENTED
	return true;
}
 
void Processor::get(char* buffer){
    /* ABOUT: Get a reply to be sent to Master.
     * -PARAMETERS:
     * -const char* buffer: pointer to char array in which to store reply.
     */

	// NOT IMPLEMENTED
}

void Processor::setStatus(int status){
	/* ABOUT: Modify Processor status.
	 * PARAMETERS:
	 * -int status: Integer code of new status to set. Must be defined in 
	 * Processor.h.
	 */

	// NOT IMPLEMENTED
}

// INNER THREAD ROUTINES ---------------------------------------------------
void Processor::_processorRoutine(void){
    /* ABOUT: To be executed by this Processor's processor thread.
     */

	// NOT IMPLEMENTED
}
     
void Processor::_blinkBlue(void){
    /* ABOUT: To be set as ISR for blue LED Ticker to show status.
     */

	// NOT IMPLEMENTED
}

/*    

    Thread processorThread; // Executes _processorRoutine

    // PROFILE DATA ------------------------------------------------------------
    int8_t fanMode;         // Single or double fan configuration
    int targetRelation[2]   // (If applic.) Rel. between front and rear fan RPM
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
    
*/