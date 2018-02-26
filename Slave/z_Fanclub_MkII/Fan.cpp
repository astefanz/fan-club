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
    initialized = false;    
}

Fan::Fan(PwmOut pwm, PinName tach, int p, int max, int min, bool test){
    
    pwmPin = new PwmOut(pwm);
    period = p;
    (*pwmPin).period_us(period);
    tachPin = tach;
    initialized = true;
    maxRPM = max;
    minRPM = min;
    active = true; // Set by default
    write(0,0,NO_DEBUG);
    
}

Fan::~Fan(){
    delete pwmPin;    
}

// READ AND WRITE

int Fan::read(bool debug){

    if(initialized) {
        
        Counter counter(tachPin); // Create temporary Counter
        int result = counter.read();

        return result;
    }
    else {

        return -1;    
    }

}

float Fan::write(float newPwm, int waitTime, bool debug){

    if(initialized and newPwm != pwm){

        *pwmPin = newPwm;
        pwm = newPwm;
  
        wait(waitTime);
        return pwm;
    }
    else{
  
        return -1;  
    }
}

// GETTERS AND SETTERS

     
int Fan::getMaxRPM(void){

     return maxRPM;    
}

int Fan::getMinRPM(void){

     return minRPM;    
}

int Fan::getPeriod(void){

     return period;
}

float Fan::getPWM(void){

     if(initialized){
        return pwm;    
     }
     else {
        return -1;    
     }
}

bool Fan::testActivity(int waitTime, bool debug){

     if(initialized){ // Check whether fan is initialized in the first place
  
        write(0.1, waitTime, debug); // Set this fan to 10%
        int rpm = read(debug);
        if ( rpm > minRPM){ // Check whether fan has responded
  
            active = true; // Set this fan as active
            return true;
        }
        else{ // If fan did not respond...

            active = false; // Set this fan as inactive
            return false;
            
        }
     }
     else{ // If the fan is not initialized, its activity is irrelevant, as it
           // is out of reach
        
        return false;
         
     }
     
}

bool Fan::isActive(void){

     
     return active;
    
}

void Fan::setPeriod(int p){
  
     period = p;
     (*pwmPin).period_us(period);
}

void Fan::setPins(PwmOut pwm, PinName tach, int max, int min){

    pwmPin = new PwmOut(pwm);
    tachPin = tach;
    initialized = true;
    maxRPM = max;
    minRPM = min;
    write(0);
}






