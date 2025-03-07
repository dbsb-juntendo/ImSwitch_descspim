#include <Arduino.h>                

// clarification: arduino is the master trigger 

int cam_out = 2;                     // from arduino to camera, exposure trigger
int cam_in = 3;                    // from camera to arduino
int exposure_time = 1;
int del = 50;

int slm_out = 4;                     // from arduino to SLM

int blanking = 5;               // blanking pin for AOTF BLUE, if high switch AOTF to on / blanking mode
int line1_aotf = A1;            // analog pin for AOTF YELLOW, set amplitude of sound wave of AOTF

int pi_stage_out = 6;           // digital from arduino to pi line 3
int pi_stage_out_2 = 8;       // digital from arduino to pi line 1
int pi_stage_in = 7;            // digital from pi to arduino

int num_trigger = 6000

;
char incomingByte;                 // for incoming serial data
int timeout = 100;

void setup() 
{
  Serial.begin(57600);      // start serial monitor

  pinMode(cam_out, OUTPUT);
  pinMode(cam_in, INPUT);

  pinMode(slm_out, OUTPUT);

  pinMode(blanking, OUTPUT);
  pinMode(line1_aotf, OUTPUT);
  digitalWrite(line1_aotf,HIGH); //sets maximum possible amplitude

  pinMode(pi_stage_out, OUTPUT);
  pinMode(pi_stage_out_2, OUTPUT);     /// line 1 digital PI stage
  pinMode(pi_stage_in, INPUT);

  Serial.println("Type input.");
}

void loop(){
 digitalWrite(cam_out, LOW);        // cam out low waiting for input
 digitalWrite(slm_out, HIGH);       // SLM idleing
 digitalWrite(line1_aotf, LOW);       // AOTF idleing
 delayMicroseconds(10);

// in order to start the loop, connect to the arduino via serial monitor, type anything and press enter
 if (Serial.available() > 0) {
   incomingByte = Serial.read();
   Serial.println(incomingByte);
   for (int i = 0; i < num_trigger; i++) {
    
    digitalWrite(slm_out, LOW);         // trigger slm
    delayMicroseconds(50);          // SLM trigger pulse
    digitalWrite(slm_out, HIGH);
    delayMicroseconds(1000);          // delay SLM to switch
    delayMicroseconds(7000);          // wait for specific time for the cam to read out all the lines before acquiring next time
                                      // the camera takes around 8 ms to read out all the lines
    
    
    // uncomment if using PI stage
    // change to 1 if no SIM grating is used
    //if (i % 15 == 0) {
    //  digitalWrite(pi_stage_out, HIGH);   // trigger PI stage
    //  delay(140);                         // time for PI stage trigger pulse
    //}

    digitalWrite(pi_stage_out, LOW);   //end PI trigger¨

    digitalWrite(cam_out, HIGH);     // trigger cam
    delayMicroseconds(del);
    digitalWrite(cam_out, LOW);        // cam out low waiting for input
    delayMicroseconds(150);            // delay for camera to reach the trigger, should be around 150 us

    while (digitalRead(cam_in) == HIGH) {  // check if cam is actually reading and if not leave laser off
      digitalWrite(line1_aotf, HIGH);      // turn on laser if camera is exposing 
      delayMicroseconds(10);               // camera is exposing, this also works if running the cam in live internal mode
    }
    digitalWrite(line1_aotf, LOW);       // turn off laser, camera is done exposing
    delayMicroseconds(10);               // jitter
    

   }
  Serial.write("Loop is done, start new!");
 }
}

