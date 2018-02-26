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

// AUXILIARY GLOBAL CONSTANTS //////////////////////////////////////////////////

const int 
          MAXRPM = 11500, /* That of the DELTA PFR0912XHE-SP00 */
          MINRPM = 0,     /* That of the DELTA PFR0912XHE-SP00 */
          STD_WAIT = 2;   /* Seconds to wait for fan to respond to PWM signal */
          
const bool DO_TEST = true,  // For testing fan activity upon initialization
           NO_TEST = false,
           NO_DEBUG = false;
           
// PINOUTS /////////////////////////////////////////////////////////////////////

// CHOOSE PINOUT:
#define v2_8

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
           
           
// CLASS INTERFACE /////////////////////////////////////////////////////////////

class Fan{
public:

    // CONSTRUCTORS AND DESTRUCTORS
    
    
    Fan();
        /* Default constructor.
         * **WARNING: THIS CLASS IS NOT DESIGNED TO BE INITIALIZED WITHOUT 
         * ARGUMENTS.
         */
    
    Fan(PwmOut pwm, PinName tach, int p = 40, int max = MAXRPM, int min = MINRPM, bool test = NO_TEST);
        /* Default constructor. Receives a pair of pins to relate to this fan and
         * the maximum and minimum RPM it can reach -- all characteristics will default to 
         * those of the DELTA PFR0912XHE-SP00
         * - PARAMETER int p: period of PWM control signal, IN MICROSECONDS
         * - PARAMETER bool test: whether to test if there is an actual fan plugged
         *   into this object's assigned pins. Defaults to NO_TEST (Defined above) 
         *   i.e do not test and assume functionality. 
         *   **NOTE** This setting is not recommended, but it is set to default 
         *   for safety purposes. This way, fans are initialized to 0% PWM
         * **WARNING** PINS GIVEN SHOULD BE CORRESPONDING PINS IN "PINOUT" ABOVE
         *   THAT HAVE NOT YET BEEN SET TO ANOTHER EXISTING FAN OBJECT. OTHERWISE,
         *   BEHAVIOR IS UNDEFINED
         */
         
    ~Fan();
        /* Destructor for class Fan
         */
         
    // READ AND WRITE
    
    int read(bool debug = NO_DEBUG);
        /* Read and return this fan's current RPM, from corresp. tach.in pin
         * - PARAMETER bool debug: whether to print out debug information to serial
         *   Defaults to NO_DEBUG (Defined atop Communicator.h)
         * - RETURNS: int, fan's current RPM, as measured by Counter (see Counter.h),
         *            or -1 if fan has not been initialized (i.e no pins have been set)
         */
    
    float write(float newPwm, int waitTime = 0, bool debug = NO_DEBUG);
        /* Set this fan's corresponding PWM out pin to given duty cycle
         * - PARAMETER float pwm: Duty cycle as percentage, between 0.0 and 1.0
         * - PARAMETER int wait: seconds to wait for fan to respond. Defaults to
         *   zero
         * - PARAMETER bool debug: whether to print out debug messages. Defaults
         *   to NO_DEBUG (false) defined atop Communicator.h
         * - RETURNS: float, given pwm if successful, -1 if fan is not initialized
         *            (i.e no pins have been set)
         */

    // GETTERS AND SETTERS
    
    int getMaxRPM(void);
        /* Return this fan's maxRPM
         */
    
    int getMinRPM(void);
        /* Return this fan's minRPM
         */
    
    int getPeriod(void);
        /* Get this fan's period (in MICROSECONDS).
         */    
    
    float getPWM(void);
        /* Return this fan's currently set pwm value
         * - PARAMETERS: void
         * - RETURNS: float, fan's current pwm set, -1 if fan is not initialized
         *            (i.e no pins have been set)
         */
         
    bool testActivity(int waitTime = 0, bool debug = NO_DEBUG);
    /* Tests this fan for activity (see definition of private member)
     * - PARAMETER int waitTime: seconds to wait for fans to adjust to test
     *   duty cycle. Defaults to zero
     * - PARAMETER bool debug: whether to print out debug information to serial
     *   defaults to NO_DEBUG (false). See const definition in Communicator.h
     * - RETURN: bool, whether an active fan has been detected.
     */
     
    bool isActive(void);
        /* Get whether this fan is currently active. (See testActivity)
         * - RETURNS bool, whether fan is active
         */    


         
         
    void setPeriod(int p);
        /* Set this fan's PWM signal period (in MICROSECONDS).
         */    
    
    void setPins(PwmOut pwm, PinName tach, int max = MAXRPM, int min = MINRPM);
        /* Set this fan's pins
         * - PARAMETERS: PwmOut pwm (pwm pin) and PinName tach (tachometer pin)
         *   along w/ max. and min. possible RPM -- will default to those of the
         *   DELTA PFR0912XHE-SP00
         * **WARNING** PINS PASSED MUST BE IN CORRESPONDING ARRAYS, AS DEFINED
         *   IN "PINOUTS" ABOVE. OTHERWISE, BEHAVIOR IS UNDEFINED.
         */
    

private:

    PwmOut*  pwmPin;         // PWM pin that connects to this fan
    PinName tachPin;        // Tachometer input pin that connects to this fan
    float pwm;               // Current duty cycle
    bool initialized;       // Whether fan object has pins assigned
    bool active;            // Whether there is an actual fan plugged in and responding
    
    int maxRPM;               // Maximum RPM
    int minRPM;               // Minimum RPM    
    int period;               // PWM period    
    
};

#endif // FAN_H
