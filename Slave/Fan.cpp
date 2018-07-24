////////////////////////////////////////////////////////////////////////////////
// INIT. TUESDAY, AUGUST 22ND, 2017  | FILE Fan.cpp
// ALEJANDRO A. STEFAN ZAVALA | CALIFORNIA INSTITUTE OF TECHNOLOGY | GALCIT
//
// FANCLUB MARK ONE | FAN OBJECT MODULE IMPLEMENTATION FILE +
////////////////////////////////////////////////////////////////////////////////

/*******************************************************************************
 * ABOUT: This file contains the implementation of the interface defined in 
 * Fan.h
 *******************************************************************************
 */

// + REVISED for prototyping FCMkII
 
#include "Fan.h"
#include "print.h"

#include "FastPWM.h"

// CONSTANT DEFINITIONS ////////////////////////////////////////////////////////
const int 
	NO_TARGET = -1;
// PINOUTS /////////////////////////////////////////////////////////////////////
    
PinName PWMS[24] = {
	PB_11,	// A	// 0 --> A
	PB_10,	// B
	PE_14,	// C
	PE_12,	// D
	PE_10,	// E
	PE_11,	// F
	PE_9,	// G
	PD_15,	// H
	PA_5,	// I
	PB_9,	// J
	PB_8,	// K
	PC_6,	// L
	PB_15,	// M
    PA_15,	// N
	PC_7,	// O
	PB_5,	// P
	PB_3,	// Q
	PB_1,	// R
	PB_6,	// S
	PD_13,	// T
	PE_6,	// U
	PE_5,	// V
	PC_9,	// W
	PC_8	// X
};

PinName TACHS[29] = {
	PF_14,	// [	// 0 --> [
	PC_2,	// '\'
	PF_4,	// ]
	PB_2,	// ^
	PD_11,	// _
	PE_0,	// `
	PG_1,	// a
	PF_9,	// b
	PF_7,	// c
	PF_8,	// d
	PE_3,	// e
	PE_4,	// f
	PD_7,	// g
	PG_3,	// h
	PG_2,	// i
	PD_2,	// j
	PC_12,	// k
	PC_11,	// l
	PC_10,	// m
	PA_3,	// n
	PC_0,	// o
	PC_3,	// p
	PF_3,	// q
	PF_5,	// r
	PF_10,	// s
	PF_2,	// t
	PF_1,	// u
	PF_0,	// v
	PG_0	// w
};	

#if 0 //------------------------------------------------------------------------
// VERSION CT1 (ADAPTED TO CAST WIND TUNNEL) ===================================
PinName vCT1[2][18] = {
	{

/*- 00 ---- 01 ---- 02 ---- 03 ---- 04 ---- 05 ---- 06 ---- 07 ---- 08 -------*/
	PE_10,	PD_13,	PB_1,	PE_9,	PB_15, 	PC_6,	PC_9,	PC_8,	PB_5,
/*- 09 ---- 10 ---- 11 ---- 12 ---- 13 ---- 14 ---- 15 ---- 16 ---- 17 -------*/
	PB_3,	PB_9,	PB_8,	PE_6,	PE_5,	PB_10,	PB_11,	PE_12,	PE_14	
	},

	{
    
/*- 00 ---- 01 ---- 02 ---- 03 ---- 04 ---- 05 ---- 06 ---- 07 ---- 08 -------*/
	PE_3,	PF_8,	PF_7,	PF_9, 	PD_11,	PB_2,	PA_3,	PD_7,	PE_0,
/*- 09 ---- 10 ---- 11 ---- 12 ---- 13 ---- 14 ---- 15 ---- 16 ---- 17 -------*/
	PG_0,	PC_2,	PF_4,	PC_3,	PC_0,	PF_5,	PF_3,	PE_4,	PF_10
	}
};
// vCT1 // =====================================================================

// VERSION 2.9 (REVISED V2.4 FOR PCB-1 w/ JPL module assignments) ==============
PinName v2_9[2][21] = {

	{
/*- 00 ---- 01 ---- 02 ---- 03 ---- 04 ---- 05 ---- 06 ---- 07 ---- 08 -------*/
    PE_11,	PE_9,	PE_14,	PE_12,	PB_11,	PB_10,	PA_15,	PC_7,	PC_6,
/*- 09 ---- 10 ---- 11 ---- 12 ---- 13 ---- 14 ---- 15 ---- 16 ---- 17 -------*/
    PB_15,	PD_15,	PA_5,	PD_13,	PE_6,	PB_3,	PB_6,	PB_9,	PB_8,
/*- 18 ---- 19 ---- 20 -------------------------------------------------------*/
    PE_5,	PC_8,	PC_9
	},
	{
    
/*- 00 ---- 01 ---- 02 ---- 03 ---- 04 ---- 05 ---- 06 ---- 07 ---- 08 -------*/
    PE_3,	PE_4,	PF_7,	PF_8,	PG_1,	PF_9,	PA_3,	PC_0,	PC_11,
/*- 09 ---- 10 ---- 11 ---- 12 ---- 13 ---- 14 ---- 15 ---- 16 ---- 17 -------*/
	PC_10,	PG_3,	PG_2,	PF_5,	PF_10,	PC_3,	PF_3,	PD_2,	PC_12,
/*- 18 ---- 19 ---- 20 -------------------------------------------------------*/
	PF_0,	PF_1,	PF_2
	}
};
// v2_9 // =====================================================================

// VERSION 2.7 (REVISED v2.4 FOR MORPHO PINOUT) ================================
#ifdef v2_7

PwmOut pwmOut[MAX_FANS] ={

/*- 00 ---- 01 ---- 02 ---- 03 ---- 04 ---- 05 ---- 06 ---- 07 ---- 08 -------*/
    PE_11,  PE_9,  PD_15,  PB_15,  PB_11,  PC_6,   PC_8,    PC_9,   PB_8,

/*- 09 ---- 10 ---- 11 ---- 12 ---- 13 ---- 14 ---- 15 ---- 16 ---- 17 -------*/
    PB_9,   PE_6,   PE_5,  PA_15,  PA_5,   PB_6,   PC_7,   PB_10,  PB_3,
                         
                   
/*- 18 ---- 19 ---- 20 -------------------------------------------------------*/
    PD_13,  PE_12,  PE_14
    
    };

PinName tachIn[MAX_FANS] ={
    
/*- 00 ---- 01 ---- 02 ---- 03 ---- 04 ---- 05 ---- 06 ---- 07 ---- 08 -------*/
    PF_3,   PF_10,  PF_5,   PA_3,   PG_1,   PF_9,   PF_8,   PF_2,   PE_4,

/*- 09 ---- 10 ---- 11 ---- 12 ---- 13 ---- 14 ---- 15 ---- 16 ---- 17 -------*/
    PG_3,   PF_0,   PF_1,   PE_3,   PC_3,   PF_7,   PC_12,  PC_10,  PC_11,
                    
/*- 18 ---- 19 ---- 20 -------------------------------------------------------*/
    PD_2,   PC_0,   PG_2           
    
    };
                          
#endif  // v2_7 // =============================================================
#endif // ----------------------------------------------------------------------

 
 
// CLASS IMPLEMENTATION ////////////////////////////////////////////////////////

// CONSTRUCTORS AND DESTRUCTORS

Fan::Fan(){
	/* ABOUT: Constructor for class Fan. Creates an uninitialized fan which
	* must be configured with Fan::configure before usage.
	*/
    initialized = false;    
} // End Fan constructor

bool Fan::configure(PinName pwmPin, PinName tachPin, uint32_t frequencyHZ,
		uint32_t counterCounts, uint8_t pulsesPerRotation, float minDC,
		uint8_t maxTimeouts){
	/* ABOUT: Configure a fan for usage. Can be called more than once.
	* PARAMETERS:
	* -PinName pwmPin: PWM pin to use for PWM control
	* -PinName tachPin: DigitalIn pin for Counter
	* -uint32_t frequencyHZ: Frequency of the PWM signal (Hz)
	* -uint32_t counterCounts: number of pulses to count
	* -uint8_t pulsesPerRotation: number of pulses for one full rotation
	* -float minDC: minimum duty cycle for nonzero RPM
	* -uint8_t maxTimeouts: maximum number of threshold misses before 
	*	chasing is aborted.
	*/
	
	if(this->initialized){
		// If the Fan is being reconfigured, deallocate previous PWM pin.
		delete this->pwmPin;
		delete this->tachPin;
	}

    this->pwmPin = new FastPWM(pwmPin);
 	this->frequencyHZ = frequencyHZ;
    (*this->pwmPin).period_us(int(1000000/this->frequencyHZ));
    this->tachPin = new PinName(tachPin);
	this->counterCounts = counterCounts;
	this->pulsesPerRotation = pulsesPerRotation;
	this->dc = 0;
	this->rpmChange = 0;
	this->pastRead = 0;
	this->target = NO_TARGET;
	this->minDC = minDC;
	this->maxTimeouts = maxTimeouts;

	this->timeouts = 0;
	
	this->pwmPin->write(double(0));
    initialized = true;

	return true;
} // End configure

Fan::~Fan(){
    delete this->pwmPin;
	delete this->tachPin;
}


int Fan::read(){
	/* ABOUT: Read the RPM of a fan. 
	* RETURNS:
	* -int, either RPM value or negative integer if the fan is 
	*	uninitialzed.
	*/
	
    if(this->initialized) {
		
        // Create temporary Counter
        Counter counter(this->tachPin, 
			this->counterCounts, this->pulsesPerRotation);         
		int read = counter.read(30000);
		this->rpmChange = this->pastRead - read;
		this->pastRead = read;
		return read;
    } else if (this->dc == 0){
		return 0;
	}
    else {

        return -1;    
    }

} // End read

bool Fan::write(float newDC){
	/* ABOUT: Set the duty cycle of a fan.
	* PARAMETERS:
	* -float newDC: new duty cycle to assign.
	* RETURNS:
	* -bool, true upon success and false upon failure (fan uninitialized)
	*/

    if(initialized and newDC != this->dc){
		//             \-----------/  Avoid redundancy
		
		// Adjust duty cycle w/ respect to boundaries:
		if(not (newDC < 1.0)){
			// DC above maximum
			this->dc = 1.0;
		} else if (newDC < this->minDC and newDC > 0.0) {
			// DC below nonzero minimum
			this->dc = minDC;
		} else if (newDC <= 0.0){
			// DC below or at 0
			this->dc = 0.0;
		} else {
			// DC within extremes
			this->dc = newDC;
		}

        this->pwmPin->write(double(this->dc));
  
        return true;
    }
    else{
  
        return false;  
    }

	return false;

} // End write

float Fan::getDC(){
	/* ABOUT: Get current duty cycle, as a float between 0.0 and 1.0.
	 * RETURNS:
	 * -float: current duty cycle, or negative code if fan is uninitialized.
	 */

	return this->initialized? this->dc : -1.0;
} // End getDC


void Fan::setTarget(int target){
	/* ABOUT: Set a target RPM for Chasing.
	* PARAMETERS:
	* -int target: target RPM.
	*/
	this->target = target;
	this->timeouts = 0;
} // End setTarget

int Fan::getTarget(){
	/* ABOUT: Get this fan's target RPM.
	 * RETURNS:
	 * -int, either the target RPM or a negative code to indicate no target is
	 * being chased. (NO_TARGET in Fan.h)
	 */	

	return this->target;

} // End getTarget


int Fan::getRPMChange(){
	/* ABOUT: Get the difference between the latest read and the past one.
	* NOTE: Will be either 0 or negative of last read if there are not enough 
	* reads so far.
	* RETURNS:
	* -int, absolute value of change in question.
	*/

	return this->rpmChange >= 0? this->rpmChange : -this->rpmChange;

} // End getDelta

bool Fan::incrementTimeouts(){
	/* ABOUT: Increment the timeout counter, and terminate chasing if it reaches
	 * the timeout threshold.
	 * RETURNS:
	 * -bool: whether the threshold was reached (false if not).
	 */
	
	if(++(this->timeouts) >= this->maxTimeouts){
		this->write(0.0);
		this->setTarget(NO_TARGET);
		return true;
	}

	return false;
} // End incrementTimeouts

void Fan::resetTimeouts(){
	/* ABOUT: Reset the timeouts counter.
	 */

	this->timeouts = 0;

} // End resetTimeouts
