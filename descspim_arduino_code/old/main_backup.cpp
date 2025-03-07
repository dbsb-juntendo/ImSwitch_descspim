#include <Arduino.h>

// button control and LED
int  buttonPin = 10;    // the pin that the pushbutton is attached to
int  ledPin = 12;       // the pin that the LED is attached to
bool buttonState = 0;         // current state of the button
bool lastButtonState = 0;     // previous state of the button
bool run_state = 0;           // current state of the run

// laser pin
int laser = 2;              // is sending the laser trigger, HIGH is on, LOW is off
int laser2 = 13;
// camerea pins

int cam_exp_in = 3;                // is reading the camera exposure trigger (green)
//int cam_read_in = 4;               // is reading the camera readout trigger(gray)
int cam_out = 5;              // is sending the camera exposure trigger (yellow)

// Stage pins
int stage_sample = 6;                // is sending the stage trigger sample
int stage_sample_in = 7;             // is reading the stage trigger sample
int stage_camera = 8;                // is sending the stage trigger objective


// variables
int trigger_delay = 2000;       // delay for camera readout trigger to go high, in µs
int exposure_time = 300;         // exposure time of camera in ms
int stage_movement_delay = 200; // delay for stage movement in ms
int max_sequence=2000;        // max number of exposures


void setup()
{
   // initialize the button pin as a input with internal pullup enabled
   pinMode(buttonPin, INPUT_PULLUP);
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

   // initialize serial communication:
   Serial.begin(9600);
   digitalWrite(ledPin, LOW);
   //digitalWrite(laser, LOW);
   //digitalWrite(laser2, LOW);
}

void loop()
{

                                                                                    
   // switch polygon on/off
   static unsigned long timer = 0;
   unsigned long interval = 1000;  // time intervall to check button state change
   if (micros() - timer >= interval)
   {
      timer = micros();
      // read the pushbutton input pin:
      buttonState = digitalRead(buttonPin);
      // compare the new buttonState to its previous state
      if (buttonState != lastButtonState)
      {
         if (buttonState == LOW)
         {
            // if the current state is LOW then the button
            // went from off to on
            // acquisition starts now
            
            // change the polygon on/off state
            Serial.println("started acquisition");
            run_state = !run_state;

         }
         lastButtonState = buttonState;
      }
      else
      {
         // if the state has not changed, check if the button is pressed
         if (run_state == HIGH)
         {  
            int laserPins[] = {laser, laser2};
            for (int i = 0; i < max_sequence; i++) {
               for (int laserID = 0; laserID < sizeof(laserPins)/sizeof(laserPins[0]); laserID++) {   // going through the lasers
                  digitalWrite(laserPins[laserID], HIGH);  
                  //digitalWrite(laser2, HIGH);      
                  digitalWrite(cam_out, HIGH);    
                  digitalWrite(ledPin, HIGH);                   
                  delay(exposure_time/2);        
                  if (digitalRead(cam_exp_in) == HIGH) {  // check if acquisition is still running from micro manager side
                     delay(exposure_time/2);             // now acquisition is done after this                      
                     digitalWrite(cam_out, LOW);   
                     digitalWrite(ledPin, LOW);                      
                        
                     // loop is done, next camera trigger is sent          
                  }
                  else {
                     // acquisition is done from micromanager, stop sending triggers and wait for next button push
                     digitalWrite(laserPins[laserID], LOW);        // turn off laser    
                     //digitalWrite(laser2, LOW);        // turn off laser
                     digitalWrite(cam_out, LOW);   
                     digitalWrite(ledPin, LOW);   
                     Serial.println("acquisition broken");
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
               // now next image is taken
               delay(200);  // delay for stage to settle, not sure if this is needed
            }
            // loop is done
            run_state = !run_state;       // acquisition stopped
            Serial.println("acquisition done");
         }
      }
   }
}


/*
Dear Max,
 
I have received the following information from our manufacturing team:
 
1) Control can be achieved via connector J2. Pins 7, 6 and 5 will activate the corresponding action (on pin diagram), if that pin is shorted (connected) to ground (pin 1). 
 
For example; If a switch is connected between the corresponding pins (i.e. between J2 pin 5 and pin 1), then the 'Forward Jog' move can be turned off and on. This might be achieved with a Arduino/Raspberry pi but would depend on how it is configured.
 
2) The 'ELL9K Evaluation Kits' also contain a hand-held controller. Control can be achieved using the handset buttons.
 
To increment the slider position, press and hold JOG, then press FW. To decrement the slider position, press and hold the JOG then press BW. To Home the stage, press the BW button.
 
3) A suitable controller (usually Windows PC) can provide RS232 serial commands. It can be controlled this way via pin 3 on connector J2. The output serial commands can be read from pin 4 on connector J2.
 
 
Let me know if this is sufficient or if you have additional questions!
 
Kind regards / Med vänliga hälsningar
*/