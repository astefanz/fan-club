////////////////////////////////////////////////////////////////////////////////
// INIT. TUESDAY, AUGUST 22ND, 2017  | FILE Counter.cpp
// ALEJANDRO A. STEFAN ZAVALA | CALIFORNIA INSTITUTE OF TECHNOLOGY | GALCIT
//
// FANCLUB MARK ONE | RPM COUNTER MODULE IMPLEMENTATION FILE
////////////////////////////////////////////////////////////////////////////////

/*******************************************************************************
 * ABOUT: This file holds the implementation of the Counter module.
 * (See Counter.h)
 *******************************************************************************
 */
 
#include "Counter.h"

 
// CONSTRUCTORS AND DESTRUCTORS

Counter::Counter(PinName pin) : interrupt(pin) {// Create the InterruptIn on the pin specified to Counter
    interrupt.rise(this, &Counter::update);// Attach increment function of this counter instance
}
    
// "READ" FUNCTION

    int Counter::read(int timeout) {
    
    // The count variable will increase by 1 with every rise (half-cycle)
    
    // Firstly, restart the timer and set the count variable so that reaches
    // 0 on the next rise
    count = -1; 
    t.reset();
    t.start();
    while(count<0 && t.read_us()<timeout){
        // Wait until the next rise (or timeout)
    }
    if (count < 0){
        return 0; // Return 0 if fan times out
    }
    // By now, count has reached 0 and both the counter variable and the 
    // timer will be syncronized at, approximately, 0
    t.reset();
    t.start();
    while(count<4 && t.read_us()<4*timeout){
        // Wait until either enough rises (or timeouts)
    }
    t.stop();   // Stop the timer as soon as the counter variable hits 1
    wait(0.001); // Let the system catch up
    if (count < 1){
        return 0; // Return 0 if the fan actually timed out
    }
    
    // Otherwise, convert from microseconds between half-cycles to RPM and return
    return count/(2*(t.read_us()/60000000.0)); 
    
}

// AUXILIARY FUNCTIONS

void Counter::update() {
        count++;
}
