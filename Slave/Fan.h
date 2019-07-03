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
#include "settings.h"

// Forward declarations:
class FastPWM;

// CONSTANT DECLARATIONS ///////////////////////////////////////////////////////
extern const int
	NO_TARGET;

// PINOUTS /////////////////////////////////////////////////////////////////////

extern PinName PWMS[24];
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

	bool configure(PinName pwmPin, PinName tachPin, int frequencyHZ,
		int counterCounts, int pulsesPerRotation, int minRPM,
		float minDC,
		int maxTimeouts);
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


    int read(Timer& timerRef, Timeout& timeoutRef, InterruptIn& interruptRef);
		/* ABOUT: Read the RPM of a fan.
		 * RETURNS:
		 * -int, either RPM value or negative integer if the fan is
		 *	uninitialzed.
		 */

		// WARNING: DO NOT USE Fan::read ON MORE THAN ONE Fan INSTANCE AT A
		// TIME. (See static InterruptIn member)

	void onInterrupt();
		/* ABOUT: To be executed w/in interrupt routine when counting pulses.
		 */

	void onTimeout();
		/* ABOUT: To be executed w/in timeout ISR
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


private:

	// General:
    FastPWM*  pwmPin;        // PWM pin that connects to this fan
    PinName* tachPin;        // Tachometer input pin that connects to this fan
    bool initialized;       // Whether fan object has pins assigned

	// For PWM control:
    int frequencyHZ;	// PWM signal frequency in Hertz
    float dc;               // Current duty cycle
	int target;				// Chaser target RPM
	int rpmChange;			// Difference between the latest read and the one before
	int pastRead;			// Previous RPM read, for RPM change
	int minRPM; 		// For RPM read timeout
	float minDC;			// Minimum duty cycle for nonzero RPM

	// For RPM reading and chasing:
	Mutex dcLock;

	Timer* timerPtr;
	Timeout* timeoutPtr;
	volatile int counts;
	volatile int timeout_us;
	volatile bool doneReading;

	int counterCounts;
	int pulsesPerRotation;
	int timeouts, maxTimeouts;

	int dbc;
	int intDC;

	static	InterruptIn interrupt;

};

#endif // FAN_H
