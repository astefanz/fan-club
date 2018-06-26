////////////////////////////////////////////////////////////////////////////////
// INIT. TUESDAY, AUGUST 22ND, 2017  | FILE Counter.cpp
//
// ** MODIFIED FOR FANCLUB MARK II **
//
// ALEJANDRO A. STEFAN ZAVALA | CALIFORNIA INSTITUTE OF TECHNOLOGY | GALCIT
//
// FANCLUB MARK ONE | RPM COUNTER MODULE IMPLEMENTATION FILE
////////////////////////////////////////////////////////////////////////////////

/*******************************************************************************
 * ABOUT: This module serves the Fan module (see Fan.h) in its function of
 * counting a fan's speed (in RPM)
 *******************************************************************************
 */
 
#ifndef COUNTER_H
#define COUNTER_H

// MBED MODULES

#include "mbed.h"

// CLASS INTERFACE /////////////////////////////////////////////////////////////

class Counter{
public:

    // CONSTRUCTORS AND DESTRUCTORS
    
    Counter(PinName* pin, uint32_t counts, uint32_t pulsesPerRotation);
        /* Constructor for class Counter
         */
    
    // "READ" FUNCTION 
    
    int read(int timeout = 30000);
        /* Measure and return the RPM of a fan connected to this Counter's pin
         * - PARAMETER int timeout: Amount of microseconds after which to assume
         * the fan is at 0 RPM; defaults to 30000us (upper bound for fan
         * DELTA PFR0912XHE-SP00
         * **NOTE** This counter is designed for fans that send "rises" every half-cycle
         * 
         */
        
        /* INFO: To measure the fan's RPM, this function will measure the time
         * between a "rise," which is to say, the time it takes for the fan to
         * complete half a cycle. The function will also keep track of a "timeout"
         * in case the fan is actually at 0 RPM
         */
    
    
private:

    InterruptIn interrupt;
    volatile int count;
	uint32_t counts, pulsesPerRotation;
    Timer t; 
    
    // AUXILIARY FUNCTIONS
    
    void update(void); 
    /* Count "up" 
     */    
    
};

#endif // COUNTER_H
