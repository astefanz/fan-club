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
#include "settings.h"

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
	PG_0,	// w
};

#if 0 //------------------------------------------------------------------------
// VERSION S117 (FOR BASEMENT AND 7x7 ARRAY PCB's) =============================
/* -----------------------------------------------------------------------------
    NOTE: Meant to be accessed using runtime pinout assignments.

    PWMS .......................................................................
    01: PE_5  :V
    02: PE_6  :U
    03: PC_8  :X
    04: PC_9  :W
    05: PD_13 :T
    06: PB_6  :S
    07: PB_3  :Q
    08: PC_7  :O
    09: PA_15 :N
    10: PB_15 :M
    11: PC_6  :L
    12: PB_8  :K
    13: PB_9  :J
    14: PA_5  :I
    15: PD_15 :H
    16: PE_9  :G
    17: PE_11 :F
    18: PE_12 :D
    19: PE_14 :C
    20: PB_10 :B
    21: PB_11 :A

    TACHS ......................................................................
    01: PH_0  :x
    02: PH_1  :y
    03: PF_2  :t
    04: PF_10 :s
    05: PF_5  :r
    06: PF_3  :q
    07: PC_3  :p
    08: PC_0  :o
    09: PA_3  :n
    10: PC_10 :m
    11: PC_11 :l
    12: PC_12 :k
    13: PD_2  :j
    14: PG_2  :i
    15: PG_3  :h
    16: PE_4  :f
    17: PE_3  :e
    18: PF_8  :d
    19: PF_7  :c
    20: PF_9  :b
    21: PG_1  :a

----------------------------------------------------------------------------- */



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
	this->timerPtr = NULL;
	this->timeoutPtr = NULL;
	this->dbc = 0;
} // End Fan constructor

bool Fan::configure(
	PinName pwmPin,
	PinName tachPin,
	int frequencyHZ,
	int counterCounts,
	int pulsesPerRotation,
	int minRPM,
	float minDC,
	int maxTimeouts
	){
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
    (*this->pwmPin).period_us(1000000/this->frequencyHZ);
    this->tachPin = new PinName(tachPin);
	this->counterCounts = counterCounts;
	this->pulsesPerRotation = pulsesPerRotation;
	this->dc = 0;
	this->intDC = 0;
	this->rpmChange = 0;
	this->pastRead = 0;
	this->target = NO_TARGET;
	this->minRPM = minRPM;
	this->minDC = minDC;

	this->timeout_us =
		(minRPM > 0? 60000000.0/minRPM : DEFAULT_FAN_TIMEOUT_US)*
		(counterCounts/pulsesPerRotation > 0 ?
			counterCounts/pulsesPerRotation : 1);

	this->counts = 0;
	this->doneReading = false;
	this->maxTimeouts = maxTimeouts;

	this->timeouts = 0;

	this->pwmPin->write(0.0);
    initialized = true;

	return true;
} // End configure

Fan::~Fan(){
    delete this->pwmPin;
	delete this->tachPin;
}


int Fan::read(Timer& timerRef, Timeout& timeoutRef, InterruptIn& interruptRef){
	/* ABOUT: Read the RPM of a fan.
	* RETURNS:
	* -int, either RPM value or negative integer if the fan is
	*	uninitialzed.
	*/

	// WARNING: DO NOT USE Fan::read ON MORE THAN ONE Fan INSTANCE AT A
	// TIME. (See static member InterruptIn)

	if (this->initialized){
		// Initialize counters and timer

		// Counter:
		this->counts = 0;

		this->timerPtr = &timerRef;
		this->timeoutPtr = &timeoutRef;

		// Timer:
		this->timerPtr->stop();
		this->timerPtr->reset();
		this->doneReading = false;

		// Timeout and interrupt:
		this->timeoutPtr->attach_us(
			callback(this, &Fan::onTimeout), this->timeout_us);

		new(&interruptRef) InterruptIn(*this->tachPin);

		interruptRef.rise(callback(this, &Fan::onInterrupt));
		//pl;printf("\n\rdbc : %d",++this->dbc);

		// Wait for interrupt to finish or timeout to expire:
		while(not this->doneReading);

		// Detach interrupt and timeout:
		interruptRef.rise(NULL);
		this->timeoutPtr->detach();
		this->timerPtr->stop();

		// Analyze results:
		int read = 0;
		if(this->counts < this->counterCounts){
			read = 0;
		} else {
			// Nonzero RPM detected.
			read = (60000000.0*this->counts)/
				(this->timerPtr->read_us()*this->pulsesPerRotation);
			/*
			pl;printf("\n\r\tCC us: %d to: %d c: %lu read: %d",
				this->timerPtr->read_us(),this->timeout_us, this->counts, read);pu;
			*/

			/* NOTE: Original form below. Form above is refactored -------------
				(this->counts/this->pulsesPerRotation) *
				(60000000.0/this->timerPtr->read_us());
			----------------------------------------------------------------- */
		}

		this->rpmChange = this->pastRead - read;
		this->pastRead = read;
		return read;

	} else {
        return -1;
    }

} // End read

void Fan::onInterrupt(void){
	/* ABOUT: To be executed w/in interrupt routine when counting pulses.
	 */

	if (this->doneReading){
		return;

	} else if (this->counts == 0){
		this->timerPtr->start();
		this->counts++;

	} else if (this->counts < this->counterCounts){
		this->counts++;

	} else{
		this->timerPtr->stop();
		this->doneReading = true;
	}

} // End onInterrupt

void Fan::onTimeout(void){
	// ABOUT: To be attached to the fan reading timeout
	this->doneReading = true;
} // End onTimeout

bool Fan::write(float newDC){
	/* ABOUT: Set the duty cycle of a fan.
	* PARAMETERS:
	* -float newDC: new duty cycle to assign.
	* RETURNS:
	* -bool, true upon success and false upon failure (fan uninitialized)
	*/

	//printf("\n\riDC: %d tDC: %d nDC: %f", this->intDC, temp, newDC);

    if(this->initialized and this->dc != newDC){
		//             \-----------/  Avoid redundancy
		//pl;printf("\n\rWriting %0.2f",this->dc);pu;

        this->pwmPin->write(newDC);

		this->dcLock.lock();
		this->dc = newDC;
		this->dcLock.unlock();

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

	if (this->initialized){
		this->dcLock.lock();
		float temp = this->dc;
		this->dcLock.unlock();

		return temp;
	} else {
		return -1.0;
	}

} // End getDC

