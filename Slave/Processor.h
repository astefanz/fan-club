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

#include "print.h"
#include "settings.h"
#include "Fan.h"

//// CONSTANT DECLARATIONS /////////////////////////////////////////////////////

extern const int  

    // STATUS CODES ------------------------------------------------------------
    CHASING,
    ACTIVE,
    OFF,
	ON,    
	TOGGLE,

    // FAN MODES ---------------------------------------------------------------
    SINGLE,
    DOUBLE;


// Process data structure ------------------------------------------------------

typedef struct{
    char content[MAX_MESSAGE_LENGTH];
} command;


//// CLASS INTERFACE ///////////////////////////////////////////////////////////

class Processor { 

public:

    // CONSTRUCTORS AND DESTRUCTORS --------------------------------------------

    Processor(void);
        /* ABOUT: Constructor for class Processor. Starts processor thread.
         */
    
    // PUBLIC INTERFACE --------------------------------------------------------
    
    bool process(const char* givenCommand, bool configure = false);
        /* ABOUT: Take a given command for processing.
         * PARAMETERS:
         * -const char* givenCommand: NULL-terminated string representing command 
         * to process.
		 * -bool configure: whether this message is to configure the Processor.
		 *	Defaults to false.
         */
         
    bool get(char* buffer);
		/* ABOUT: Get a reply to be sent to Master.
		 * PARAMETERS:
		 * -const char* buffer: pointer to char array in which to store reply.
		 * RETURNS:
		 * -bool: whether a new message was fetched (false for default)
		 *	NOTE: a false return value implies the given buffer has been left 
		 * 	unmodified.
		 */

    void setStatus(int status = OFF);
        /* ABOUT: Modify Processor status.
         * PARAMETERS:
         * -int status: Integer code of new status to set. Must be defined in 
         * Processor.h.
         */
    
    void start(void);
    
private:

    // INNER THREAD ROUTINES ---------------------------------------------------
    void _processorRoutine(void);
        /* ABOUT: To be executed by this Processor's processor thread.
         */
         
    void _setLED(int state = OFF);
        /* ABOUT: Set LED state.
         */
         
	void _blinkLED(void);
		/* ABOUT: To be set as ISR for blue LED Ticker to show status.
		 */
    Thread processorThread; // Executes _processorRoutine
    
    // PROFILE DATA ------------------------------------------------------------
    int8_t fanMode;         // Single or double fan configuration
    uint8_t activeFans;     // Number of active fans
	uint32_t fanFrequencyHZ;	// PWM frequency of fans
    uint8_t counterCounts;  // Number of pulses to be counted when reading
    uint8_t pulsesPerRotation;   // Pulses sent by sensor in one full rotation
    uint32_t maxRPM;         // Maximum nominal RPM of fan model
    uint32_t minRPM;         // Minimum nominal nonzero RPM of fan model
    float minDC;          // Duty cycle corresponding to minRPM (nominal)
	float chaserTolerance;
	uint8_t maxFanTimeouts;
	uint32_t dataIndex;		// Index for new data
	float rpmSlope;
    
	// STATUS DATA -------------------------------------------------------------
    int8_t status;      // Current processor status
    DigitalOut led 
		,xled, psuOff;    // Access to blue LED
    Ticker blinker;     // Used to blink blue LED for status    
	Mutex threadLock;
    // PROCESS DATA ------------------------------------------------------------
	
	//			INPUT			OUTPUT
	bool		inFlag,			outFlag; 		// Track buffer state
	Mutex		inFlagLock,		outFlagLock;	// Protect input flags

	//			BUFFERS:
	char		inBuffer[MAX_MESSAGE_LENGTH],
				outBuffer[MAX_MESSAGE_LENGTH];

    // Fan array data ----------------------------------------------------------
    Fan fanArray[MAX_FANS];
    
};


#endif // PROCESSOR_H

