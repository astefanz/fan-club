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

// CONSTANT DEFINITIONS ////////////////////////////////////////////////////////
const int 
	NO_TARGET = -1;

// PINOUTS /////////////////////////////////////////////////////////////////////

// VERSION 2.8 (REVISED V2.4 FOR PCB-1) ========================================
#ifdef v2_8

PwmOut pwmOut[MAX_FANS] ={

/*- 00 ---- 01 ---- 02 ---- 03 ---- 04 ---- 05 ---- 06 ---- 07 ---- 08 -------*/
    PE_5,  PE_6,  PC_8,   PC_9,  PD_13,   PB_6,    PB_3,    PC_7,   PA_15,

/*- 09 ---- 10 ---- 11 ---- 12 ---- 13 ---- 14 ---- 15 ---- 16 ---- 17 -------*/
    PB_15,  PC_6,  PB_8,  PB_9,   PA_5,   PD_15,   PE_9,  PE_11,  PE_12,
                         
                   
/*- 18 ---- 19 ---- 20 -------------------------------------------------------*/
    PE_14,  PB_10,  PB_11
    
    };

PinName tachIn[MAX_FANS] ={
    
/*- 00 ---- 01 ---- 02 ---- 03 ---- 04 ---- 05 ---- 06 ---- 07 ---- 08 -------*/
    PF_0,   PF_1,  PF_2,   PF_10,   PF_5,   PF_3,   PC_3,   PC_0,   PA_3,

/*- 09 ---- 10 ---- 11 ---- 12 ---- 13 ---- 14 ---- 15 ---- 16 ---- 17 -------*/
    PC_10,  PC_11,  PC_12,  PD_2,   PG_2,   PG_3,   PE_4,  PE_3,  PF_8,
                    
/*- 18 ---- 19 ---- 20 -------------------------------------------------------*/
    PF_7,   PF_9,   PG_1           
    
    };

#endif // v2_8 // ==============================================================

// VERSION 2.8J(REVISED V2.4 FOR PCB-1, ADAPTED TO JPL MODULES) ================
#ifdef v2_8J

PwmOut pwmOut[MAX_FANS] ={

/*- 00 ---- 01 ---- 02 ---- 03 ---- 04 ---- 05 ---- 06 ---- 07 ---- 08 -------*/                             
    PE_5,  PE_6,  PC_8,   PC_9,  PD_13,   PB_6,    PB_3,    PC_7,
    
    };

PinName tachIn[MAX_FANS] ={
    
/*- 00 ---- 01 ---- 02 ---- 03 ---- 04 ---- 05 ---- 06 ---- 07 ---- 08 -------*/
    PF_0,   PF_1,  PF_2,   PF_10,   PF_5,   PF_3,   PC_3,   PC_0,         
    
    };

#endif // v2_8J // =============================================================

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
 
 
// CLASS IMPLEMENTATION ////////////////////////////////////////////////////////

// CONSTRUCTORS AND DESTRUCTORS

Fan::Fan(){
	/* ABOUT: Constructor for class Fan. Creates an uninitialized fan which
	* must be configured with Fan::configure before usage.
	*/
    initialized = false;    
} // End Fan constructor

bool Fan::configure(PwmOut pwmPin, PinName tachPin, uint32_t frequencyHZ,
		uint32_t counterCounts, uint8_t pulsesPerRotation, float minDC,
		uint8_t maxTimeouts){
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
	
	if(this->initialized){
		// If the Fan is being reconfigured, deallocate previous PWM pin.
		delete this->pwmPin;
	}

    this->pwmPin = new PwmOut(pwmPin);
 	this->frequencyHZ = frequencyHZ;
    (*this->pwmPin).period_us(1000000/this->frequencyHZ);
    this->tachPin = tachPin;
	this->counterCounts = counterCounts;
	this->pulsesPerRotation = pulsesPerRotation;
	this->rpmChange = 0;
	this->pastRead = 0;
	this->target = NO_TARGET;
	this->minDC = minDC;
	this->maxTimeouts = maxTimeouts;

	this->timeouts = 0;
	
	this->write(0); 
    initialized = true;

	return true;
} // End configure

Fan::~Fan(){
    delete this->pwmPin;    
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
		int read = counter.read();
		this->rpmChange = this->pastRead - read;
		this->pastRead = read;
		return read;
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
		} else {
			// Acceptable DC
			this->dc = newDC;
		}

        this->pwmPin->write(this->dc);
  
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
