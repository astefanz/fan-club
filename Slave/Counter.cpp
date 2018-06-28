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
#include "print.h"
 
// CONSTRUCTORS AND DESTRUCTORS

Counter::Counter(PinName* pin, uint32_t counts, uint32_t pulsesPerRotation): 
	interrupt(*pin), counts(counts), pulsesPerRotation(pulsesPerRotation)
{// Create the InterruptIn on the pin specified to Counter
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
    while(count<1 && t.read_us()<timeout){
        // Wait until either the next rise (or timeout)
    }
    t.stop();   // Stop the timer as soon as the counter variable hits 1
    //wait(0.001); // Let the system catch up ------------------------------(1)
    if (count < 1){
        return 0; // Return 0 if the fan actually timed out
    }

    // Otherwise, convert from microseconds between half-cycles to RPM and return
    return 1/(2*(t.read_us()/60000000.0));
	
	#if 0
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
		/* DEBUG
		pl;printf(
		"\n\r\tCounter timed out after %dus (2)",this->counts, t.read_us());pu;
        */
		return 0; // Return 0 if fan times out
    }
    // By now, count has reached 0 and both the counter variable and the 
    // timer will be syncronized at, approximately, 0
    t.reset();
    t.start();
    while(count< this->counts && t.read_us()< this->counts*timeout){
        // Wait until either enough rises (or timeouts)
    }
    t.stop();   // Stop the timer as soon as the counter variable hits 1
    wait(0.001); // Let the system catch up
    if (count < 1){
		/* DEBUG
		pl;printf("\n\r\tCounter timed out after %dus (3)",this->counts, t.read_us());pu;
         */
		return 0; // Return 0 if the fan actually timed out
    }
    
	/* DEBUG		
	pl;printf("\n\r\tCounted %d spins in %dus",this->counts, t.read_us());pu;
	 */
	/* DEBUG
	pl;printf("\n\r\tReturning: %d RPM",
		1 / pulsesPerRotation*(t.read_us()/(this->counts*6000000.0)));pu;
	*/

	pl;printf("\n\r\tcounts:%d, ppr: %d, timeout: %d, count: %d, seconds: %f",
		this->counts, this->pulsesPerRotation, timeout, this->count,
		t.read());pu;

	pl;printf("\n\rReturning (as int): %f",
		 ((counts/float(pulsesPerRotation))/(t.read()*60.0)));


	return int((counts/float(pulsesPerRotation))/(t.read()*60.0));

	#if 0
    // Otherwise, convert from microseconds between half-cycles to RPM and return
    return  1 / pulsesPerRotation*(t.read_us()/(this->counts*6000000.0));
		// count/(2*(t.read_us()/60000000.0));

	#endif
	#endif

} // End read

// AUXILIARY FUNCTIONS

void Counter::update() {
        count++;
}
