#include <Arduino.h>

// button control and LED
int  ledPin = 12;             // the pin that the LED is attached to

// PIN 8 488
// PIN 2 594
// laser pin
int laser = 8;                // is sending the laser trigger, HIGH is on, LOW is off
int laser2 = 2;
int laser3 = 2;               // for when using the same laser twice

// camera pins
int cam_exp_in = 3;           // is reading the camera exposure trigger (green)
int cam_out = 4;              // is sending the camera exposure trigger (yellow)

// Stage pins
int stage_sample = 5;         // is sending the stage trigger sample
int stage_sample_in = 6;      // is reading the stage trigger sample
int stage_camera = 7;         // is sending the stage trigger objective

// Filter slider pins
int ell9_in_motion = 9;        // in motion
int ell9_jog_mode = 10;         // jog mode
int ell9_backward = 11;        // backward
int ell9_forward = 12;         // forward

/*
Pin 	Type 	Function
1 	PWR 	Ground
2 	OUT 	OTDX - Open Drain Transmit 3.3 V TTL RS232
3 	IN 	RX Receive 3.3 V TTL RS232
4 	OUT 	In Motion, Open Drain Active Low Max 5 mA
5 	IN 	JOG/Mode, Active Low Max 5 V
6 	IN 	BW Backward, Active Low Max 5 V
7 	IN 	FW Forward, Active Low Max 5 V
8 	PWR 	VCC +5 V ± 10%; 1200 mA
*/

// variables
int trigger_delay = 2000;        // delay for camera readout trigger to go high, in µs
int exposure_time = 300;         // exposure time of camera in ms
int stage_movement_delay = 200;  // delay for stage movement in ms
int max_sequence=2000;           // max number of exposures
char incomingByte;               // for incoming serial data
bool run_state = 0;              // current state of the run
int sliderState = 0;             // current state of the slider
int movePin = ell9_forward;      // start with forward movement


// reverse array
void reverseArray(int arr[], int length) {
  for (int i = 0; i < length / 2; i++) {
    int temp = arr[i];
    arr[i] = arr[length - 1 - i];
    arr[length - 1 - i] = temp;
  }
}

void setup()
{
   // initialize the button pin as a input with internal pullup enabled
   // initialize the LED as an output:
   pinMode(ledPin, OUTPUT);

   // laser pin
   pinMode(laser, OUTPUT);
   pinMode(laser2, OUTPUT);
   // cam pins
   pinMode(cam_out, OUTPUT);
   //pinMode(cam_read_in, INPUT);
   pinMode(cam_exp_in, INPUT);

   // stage pins
   pinMode(stage_sample, OUTPUT);
   pinMode(stage_sample_in, INPUT);
   pinMode(stage_camera, OUTPUT);

   // filter slider pins
   pinMode(ell9_in_motion, INPUT);
   pinMode(ell9_jog_mode, OUTPUT);
   pinMode(ell9_backward, OUTPUT);
   pinMode(ell9_forward, OUTPUT);

   // home filter slider
   digitalWrite(ell9_jog_mode, HIGH);
   digitalWrite(ell9_forward, HIGH);
   digitalWrite(ell9_backward, HIGH);
   delay(100);
   digitalWrite(ell9_backward, LOW);      // home
   delay(100);
   digitalWrite(ell9_backward, HIGH);
   delay(5000);
   
   // initialize serial communication:
   Serial.begin(9600);
   digitalWrite(ledPin, LOW);

}


void loop()
{
   delayMicroseconds(10);
   digitalWrite(laser, LOW);
   digitalWrite(laser2, LOW);
   if (Serial.available() > 0) {
      incomingByte = Serial.read();
      Serial.println(incomingByte);
      run_state = 1;
      int laserPins[] = {laser2};//, laser2, laser3};
      int arrayLength = sizeof(laserPins) / sizeof(laserPins[0]);

      //int sliderMovePins[] = {ell9_forward, ell9_backward};
      //int sliderMoveLength = sizeof(sliderMovePins) / sizeof(sliderMovePins[0]);

      for (int i = 0; i < max_sequence; i++) {
         if (run_state == 0) {
            Serial.println("run_state is 0");
            break;
         }

         for (int laserID = 0; laserID < arrayLength; laserID++) {   // going through the lasers

            digitalWrite(laserPins[laserID], HIGH);  
            Serial.print("Laser ID: ");
            Serial.println(laserPins[laserID]);

            digitalWrite(cam_out, HIGH);    
            digitalWrite(ledPin, HIGH);                   
            delay(exposure_time/2);       
            if (digitalRead(cam_exp_in) == HIGH) {  // check if acquisition is still running from micro manager side
               delay(exposure_time/2);             // now acquisition is done after this                      
               digitalWrite(cam_out, LOW);   
               digitalWrite(ledPin, LOW);                      
               digitalWrite(laserPins[laserID], LOW);   

               // todo make faster by only adding the delay if stage is NOT moved
               delay(40);  // cam_readout_delay  , should be 1000/30.15 = 33.2 ms, is stopping the acquisition sometimes due to overflow buffer error
               
               // move the slider
               //if statement here whether to move the slider or not
               if (sliderState < 2 && arrayLength > 1) {    // only move if slider state is 0 or 1 AND there are more than 1 laser
                  digitalWrite(ell9_jog_mode, LOW);                        
                  digitalWrite(movePin, LOW);
                  delay(50);
                  digitalWrite(movePin, HIGH);
                  digitalWrite(ell9_jog_mode, HIGH);
                  delay(100);
                  while (digitalRead(ell9_in_motion) == LOW) {
                     delay(10);        //check if slider is still in motion
                  }
                  sliderState += 1;
               }
            }

            else {
               // acquisition is done from micromanager, stop sending triggers and wait for next button push
               digitalWrite(laserPins[laserID], LOW);        // turn off laser    
               Serial.print("Laser ID: off");
               Serial.println(laserID);
               
               digitalWrite(cam_out, LOW);   
               digitalWrite(ledPin, LOW);   
               Serial.println("acquisition broken");
               run_state = 0;
               break;
               }
         }

         // move stage now
         digitalWrite(stage_sample, HIGH);     // trsigger stage 1
         digitalWrite(stage_camera, HIGH);     // trigger stage 2
         delayMicroseconds(trigger_delay);     // delay for stage movement
         digitalWrite(stage_sample, LOW);     // end stage 1 trigger
         digitalWrite(stage_camera, LOW);     // end stage 2 trigger
         while (digitalRead(stage_sample_in) == HIGH) {  // check if stage is still moving
            delayMicroseconds(10);          
         }

         reverseArray(laserPins, arrayLength);        // reverse laserpins array 
         if (movePin == ell9_forward){                // reverse slider movement direction
            movePin = ell9_backward;
         }
         else {
            movePin = ell9_forward;
         }

      }
   }
}


/*
Dear Max,
 
I have received the following information from our manufacturing team:
 
1) Control can be achieved via connector J2. Pins 7, 6 and 5 will activate the corresponding action 
(on pin diagram), if that pin is shorted (connected) to ground (pin 1). 
 
For example; If a switch is connected between the corresponding pins (i.e. between J2 pin 5 and pin 1), 
then the 'Forward Jog' move can be turned off and on. This might be achieved with a Arduino/Raspberry pi 
but would depend on how it is configured.

micromanager comments
ex 488, 594
em 705/72
exposure 300
laser 10mW, 150mW
cam_stage 42DU
sample_stage 11DU
sample intestine
lightsheet 6mm

*/