#include "mbed.h"
#include "FastPWM.h"


#define VERSION "2"

DigitalOut redLED(LED3), blueLED(LED2);
Timer timer;
InterruptIn button(USER_BUTTON);


FastPWM pwms[18] =	{

/*- 00 ---- 01 ---- 02 ---- 03 ---- 04 ---- 05 ---- 06 ---- 07 ---- 08 -------*/
	PE_10,	PD_13,	PB_1,	PE_9,	PB_15, 	PC_6,	PC_9,	PC_8,	PB_5,
/*- 09 ---- 10 ---- 11 ---- 12 ---- 13 ---- 14 ---- 15 ---- 16 ---- 17 -------*/
	PB_3,	PB_9,	PB_8,	PE_6,	PE_5,	PB_10,	PB_11,	PE_12,	PE_14	
};

bool tflag = false;

void isr(void){
	tflag = !tflag;
	blueLED = tflag;
}

int main(){

	printf("\n\rInterrupt test started (VERSION \"%s\")", VERSION);
	redLED = 1;
	blueLED = 0;

	button.rise(&isr);

	for(int i = 0; i < 18; i++){
		pwms[i].period_us(40);
		pwms[i].write(.1);
	}
	
	printf("\n\rSet to 10%% DC");
	
	timer.start();

	while(true){
	
		if(tflag){
			timer.read_us();
			timer.stop();
			timer.reset();
			timer.start();
		}

	
	}

	return 0;
}
