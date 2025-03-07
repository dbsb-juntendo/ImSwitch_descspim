#include <Arduino.h>

// button control and LED
//int  buttonPin = 10;    // the pin that the pushbutton is attached to
int  ledPin = 13;       // the pin that the LED is attached to
//bool buttonState = 0;         // current state of the button
//bool lastButtonState = 0;     // previous state of the button
//bool run_state = 0;           // current state of the run

// laser pin
int aotf_channel_1 = A1;              // is sending the laser trigger, HIGH is on, LOW is off
int aotf_blanking = A2;               // is sending the laser blanking trigger, HIGH is on, LOW is off

//int laser2 = 13;
// camerea pins

//int cam_exp_in = 3;                // is reading the camera exposure trigger (green)
//int cam_read_in = 4;               // is reading the camera readout trigger(gray)
//int cam_out = 5;              // is sending the camera exposure trigger (yellow)

// Stage pins
//int stage_sample = 5;         // is sending the stage trigger sample
//int stage_sample_in = 6;      // is reading the stage trigger sample
//int stage_camera = 2;         // is sending the stage trigger objective
//int ell9_in_motion = 9;        // in motion
//int ell9_jog_mode = 10;         // jog mode
// ell9_backward = 11;        // backward
//int ell9_forward = 12;         // forward


// variables
int trigger_delay = 4000;       // delay for camera readout trigger to go high, in µs
int exposure_time = 300;         // exposure time of camera in ms
//int stage_movement_delay = 200; // delay for stage movement in ms
//int max_sequence=1000;        // max number of exposures


void setup()
{
   // initialize the button pin as a input with internal pullup enabled
   //pinMode(buttonPin, INPUT_PULLUP);
   // initialize the LED as an output:
   pinMode(ledPin, OUTPUT);

   // laser pin
   pinMode(aotf_channel_1, OUTPUT);
   pinMode(aotf_blanking, OUTPUT);

   digitalWrite(aotf_channel_1, HIGH);
   //pinMode(laser2, OUTPUT);
   // cam pins
   //pinMode(stage_camera, OUTPUT);
   //pinMode(cam_read_in, INPUT);
   //pinMode(cam_exp_in, INPUT);

   // stage pins
   //pinMode(stage_sample, OUTPUT);
   //pinMode(stage_sample_in, INPUT);
}

void loop()
{   
   digitalWrite(ledPin, HIGH);
   digitalWrite(aotf_channel_1, HIGH);
   delay(3000);
   digitalWrite(ledPin, LOW);
   digitalWrite(aotf_channel_1, LOW);
   delay(3000);


   //digitalWrite(ell9_jog_mode, LOW);
   //delay(5000);

}


/*
   unsigned long startTime = millis(); // get the current time
   while (millis() - startTime < exposure_time) {
      // continue looping until 300 ms have passed
      Serial.println("___              I   :HIGH, exposing...");
      delayMicroseconds(50);
   }

   unsigned long startTime2 = millis(); // get the current time
   while (millis() - startTime2 < trigger_delay) {
      // continue looping until 300 ms have passed
      Serial.println("___   I              :LOW");
      delayMicroseconds(50);
   }                                                                                    
}
*/