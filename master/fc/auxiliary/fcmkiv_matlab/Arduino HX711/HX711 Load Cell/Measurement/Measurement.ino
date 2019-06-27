 
/*
 Example using the SparkFun HX711 breakout board with a scale
 By: Nathan Seidle
 SparkFun Electronics
 Date: November 19th, 2014
 License: This code is public domain but you buy me a beer if you use this and we meet someday (Beerware license).

 This example demonstrates basic scale output. See the calibration sketch to get the calibration_factor for your
 specific load cell setup.

 This example code uses bogde's excellent library: https://github.com/bogde/HX711
 bogde's library is released under a GNU GENERAL PUBLIC LICENSE

 The HX711 does one thing well: read load cells. The breakout board is compatible with any wheat-stone bridge
 based load cell which should allow a user to measure everything from a few grams to tens of tons.
 Arduino pin 2 -> HX711 CLK
 3 -> DAT
 5V -> VCC
 GND -> GND

 The HX711 board can be powered from 2.7V to 5V so the Arduino 5V power should be fine.

*/

#include "HX711.h"

#define calibration_factor -125840.00//Drag Reading
#define calibration_factor2 -308390.00 //Lift Reading


#define DOUT  3        // Drag Load Cell
#define CLK  2
#define DOUT2  5    // Lift Load Cell
#define CLK2  4

HX711 scale(DOUT, CLK);
HX711 scale2(DOUT2, CLK2);

void setup() {
  Serial.begin(9600);

  //Serial.println("HX711 scale demo");

  scale.set_scale(calibration_factor); //This value is obtained by using the SparkFun_HX711_Calibration sketch
   scale2.set_scale(calibration_factor2); //This value is obtained by using the SparkFun_HX711_Calibration sketch

   
  scale.tare(); //Assuming there is no weight on the scale at start up, reset the scale to 0
  scale2.tare(); //Assuming there is no weight on the scale at start up, reset the scale to 0
  


  
   

}

void loop() {
 // Serial.print("Readings Scale 1:");
  Serial.println(scale.get_units()*1000, 2);
 // Serial.print(" g"); //You can change this to kg but you'll need to refactor the calibration_factor
// Serial.println();
 //Serial.print("Readings Scale 2:");
  Serial.println(scale2.get_units()*1000, 2);
 // Serial.print(" g"); //You can change this to kg but you'll need to refactor the calibration_factor
// Serial.println();


  
}
