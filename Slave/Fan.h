////////////////////////////////////////////////////////////////////////////////
// INIT. TUESDAY, AUGUST 22ND, 2017  | FILE Fan.h
// ALEJANDRO A. STEFAN ZAVALA | CALIFORNIA INSTITUTE OF TECHNOLOGY | GALCIT
//
// FANCLUB MARK ONE | FAN OBJECT MODULE INTERFACE FILE
////////////////////////////////////////////////////////////////////////////////

/*******************************************************************************
 * ABOUT: This module represents a fan physically connected to this board, and
 * handles all operations on said fan.
 *******************************************************************************
 */
 
#ifndef FAN_H
#define FAN_H

// MBED MODULES
#include "mbed.h"

// CUSTOM MODULES
#include "Counter.h"
#include "settings.h"


// CONSTANT DECLARATIONS ///////////////////////////////////////////////////////
extern const int 
	NO_TARGET;
           
// PINOUTS /////////////////////////////////////////////////////////////////////

extern PwmOut PWMS[24];
extern PinName TACHS[29];

#if 0 // -----------------------------------------------------------------------
// VERSION CT1 (ADAPTED TO CAST WIND TUNNEL) ===================================
#ifdef vCT1
#define PINOUT_NAME  "vCT1"
#define MAX_FANS 18

extern PwmOut pwmOut[MAX_FANS];

extern PinName tachIn[MAX_FANS];

#endif // vCT1 // ==============================================================

// VERSION 2.9 (REVISED V2.4 FOR PCB-1 W JPL FAN ASSIGNMENTS) ==================
#ifdef v2_9
#define PINOUT_NAME  "v2.9"
#define MAX_FANS 21

extern PwmOut pwmOut[MAX_FANS];

extern PinName tachIn[MAX_FANS];

#endif // v2_9 // ==============================================================

// VERSION 2.8 (REVISED V2.4 FOR PCB-1) ========================================
#ifdef v2_8
#define PINOUT_NAME  "v2.8"
#define MAX_FANS 21

extern PwmOut pwmOut[MAX_FANS];

extern PinName tachIn[MAX_FANS];

#endif // v2_8 // ==============================================================

// VERSION 2.8J(REVISED V2.4 FOR PCB-1, ADAPTED TO JPL MODULES) ================
#ifdef v2_8J
#define PINOUT_NAME  "v2.8J"
#define MAX_FANS 8

extern PwmOut pwmOut[MAX_FANS];

extern PinName tachIn[MAX_FANS];

#endif // v2_8J // =============================================================

// VERSION 2.7 (REVISED v2.4 FOR MORPHO PINOUT) ================================
#ifdef v2_7
#define PINOUT_NAME  "v2.7"
#define MAX_FANS 21

extern PwmOut pwmOut[MAX_FANS];

extern PinName tachIn[MAX_FANS];
                          
#endif  // v2_7 // =============================================================
#endif // ----------------------------------------------------------------------
           
// CLASS INTERFACE /////////////////////////////////////////////////////////////

class Fan{
public:
    // CONSTRUCTORS AND DESTRUCTORS 
    Fan();
		/* ABOUT: Constructor for class Fan. Creates an uninitialized fan which
		 * must be configured with Fan::configure before usage.
		 */
         
    ~Fan();
		/* ABOUT: Destructor for class Fan.
		 */
         
	bool configure(PwmOut pwmPin, PinName tachPin, uint32_t frequencyHZ,
		uint32_t counterCounts, uint8_t pulsesPerRotation, float minDC,
		uint8_t maxTimeouts);
		/* ABOUT: Configure a fan for usage. Can be called more than once.
		 * PARAMETERS:
		 * -PwmOut pwmPin: PWM pin to use for PWM control
		 * -PinName tachPin: DigitalIn pin for Counter
		 * -uint32_t frequencyHZ: Frequency of the PWM signal (Hz)
		 * -uint32_t counterCounts: number of pulses to count
		 * -uint8_t pulsesPerRotation: number of pulses for one full rotation
		 * -float minDC: minimum duty cycle for nonzero RPM
		 * -uint8_t maxTimeouts: maximum number of threshold misses before 
		 *	chasing is aborted.
		 */


    int read();
		/* ABOUT: Read the RPM of a fan. 
		 * RETURNS:
		 * -int, either RPM value or negative integer if the fan is 
		 *	uninitialzed.
		 */
    
    bool write(float newDC);
 		/* ABOUT: Set the duty cycle of a fan.
		 * PARAMETERS:
		 * -float newDC: new duty cycle to assign.
		 * RETURNS:
		 * -bool, true upon success and false upon failure (fan uninitialized)
		 */

	float getDC();
		/* ABOUT: Get current duty cycle, as a float between 0.0 and 1.0.
		* RETURNS:
		* -float: current duty cycle, or negative code if fan is uninitialized.
		*/

	void setTarget(int target);
		/* ABOUT: Set a target RPM for Chasing.
		 * PARAMETERS:
		 * -int target: target RPM.
		 */

	int getTarget();
		/* ABOUT: Get this fan's target RPM.
		* RETURNS:
		* -int, either the target RPM or a negative code to indicate no target is
		* being chased. (NO_TARGET in Fan.h)
		*/	

	int getRPMChange();
		/* ABOUT: Get the difference between the latest read and the past one.
		* NOTE: Will be either 0 or negative of last read if there are not enough 
		* reads so far.
		* RETURNS:
		* -int, absolute value of change in question.
		*/

	bool incrementTimeouts();
		/* ABOUT: Increment the timeout counter, and terminate chasing if it reaches
		* the timeout threshold.
		* RETURNS:
		* -bool: whether the threshold was reached (false if not).
		*/

	void resetTimeouts();
		/* ABOUT: Reset the timeouts counter.
 		 */

private:

	// General:
    PwmOut*  pwmPin;        // PWM pin that connects to this fan
    PinName* tachPin;        // Tachometer input pin that connects to this fan
    bool initialized;       // Whether fan object has pins assigned

	// For PWM control:
    uint32_t frequencyHZ;	// PWM signal frequency in Hertz
    float dc;               // Current duty cycle
	int target;				// Chaser target RPM
	int rpmChange;			// Difference between the latest read and the one before
	int pastRead;			// Previous RPM read, for RPM change
	float minDC;			// Minimum duty cycle for nonzero RPM

	// For RPM reading and chasing:
	uint32_t counterCounts;
	uint8_t pulsesPerRotation;	
	uint8_t timeouts, maxTimeouts;

};

#endif // FAN_H
