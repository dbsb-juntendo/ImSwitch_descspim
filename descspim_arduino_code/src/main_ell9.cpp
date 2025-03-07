#include <Arduino.h>


// button control and LED
int ledPin = 13;       // the pin that the LED is attached to

int laser = 8;                // 488
int laser2 = 2;               // 594
int aotf_channel_1 = 5;      // 561
int aotf_blanking = 7;      // blanking

// camera pins
int cam_exp_in = 3;           // is reading the camera exposure trigger (green)
int cam_out = 4;              // is sending the camera exposure trigger (yellow)

// Stage pins
int stage_sample = A1;         // is sending the stage trigger sample, before 5
int stage_sample_in = 6;      // is reading the stage trigger sample
int stage_camera = A2;         // is sending the stage trigger objective, before 7

// filter slider pins
int ell9_in_motion = 9;        // in motion
int ell9_jog_mode = 10;         // jog mode
int ell9_backward = 11;        // backward
int ell9_forward = 12;         // forward

const int HOME = 1;
const int MAX_POS = 4;
int current_pos = HOME;               // position pin,  0 is pos 1, 
                                        //       1 is pos 2, 
                                        //       2 is pos 3, 
                                        //       3 is pos 4

void setup()
{
   // initialize Serial
   Serial.begin(9600);
   // initialize the LED as an output:
   pinMode(ledPin, OUTPUT);
   
   // laser pin
   pinMode(laser, OUTPUT);
   pinMode(laser2, OUTPUT);
   pinMode(aotf_blanking, OUTPUT);
   pinMode(aotf_channel_1, OUTPUT);
   digitalWrite(aotf_channel_1,HIGH); //sets maximum possible amplitude
   digitalWrite(aotf_channel_1,LOW); //sets maximum possible amplitude

   // cam pins
   pinMode(cam_out, OUTPUT);
   pinMode(cam_exp_in, INPUT);

   // stage pins
   pinMode(stage_sample, OUTPUT);
   pinMode(stage_sample_in, INPUT);
   pinMode(stage_camera, OUTPUT);
   // slider pins
   pinMode(ell9_in_motion, INPUT);
   pinMode(ell9_jog_mode, OUTPUT);
   pinMode(ell9_backward, OUTPUT);
   pinMode(ell9_forward, OUTPUT);

   // initialize serial communication:
   digitalWrite(ledPin, LOW);
   digitalWrite(ell9_jog_mode, HIGH);
   digitalWrite(ell9_forward, HIGH);
   digitalWrite(ell9_backward, HIGH);
   delay(500);

   // homing
   digitalWrite(ell9_backward, LOW);
   //Serial.println("Homing...");
   delay(100);
   digitalWrite(ell9_backward, HIGH);
   delay(1000);
   //Serial.println("Homing done");
}

// move filter slider forward or backward
void move(int movePin) {   
    digitalWrite(ell9_jog_mode, LOW);
    digitalWrite(movePin, LOW);
    delay(100);
    digitalWrite(movePin, HIGH);
    digitalWrite(ell9_jog_mode, HIGH);
    while (digitalRead(ell9_in_motion) == LOW) {
        delay(10);
    }
    delay(200);             // may remove in the end, for safety
}

// homing filder slider
void home(){
    digitalWrite(ell9_jog_mode, HIGH);
    digitalWrite(ell9_forward, HIGH);
    digitalWrite(ell9_backward, HIGH);
    delay(100);
    digitalWrite(ell9_backward, LOW);      // home
    delay(100);
    digitalWrite(ell9_backward, HIGH);
    delay(5000);
}

// reverse array
void reverseArray(int arr[], int length) {
  for (int i = 0; i < length / 2; i++) {
    int temp = arr[i];
    arr[i] = arr[length - 1 - i];
    arr[length - 1 - i] = temp;
  }
}

// move filter slider to a specific position
void move_to(int targetPos) {
    if (targetPos == 0) {
        //Serial.println("Homing...");
        home();
        //Serial.println("Homing done");
        current_pos = HOME;
        return;
    }
    else if (targetPos < 0 or targetPos > 4) {
        //Serial.println("Invalid position");
        return;
    }
    else if (targetPos == current_pos) {
        //Serial.println("Already at the target position");
    }
    else if (targetPos >= HOME && targetPos <= MAX_POS) {
        //Serial.print("Moving to position: ");
        //Serial.println(targetPos);
        while (current_pos != targetPos) {
            if (current_pos < targetPos) {
                move(ell9_forward);
                current_pos++;
            } else if (current_pos > targetPos) {
                move(ell9_backward);
                current_pos--;
            }
        }
        //Serial.println("Movement done, new position:");
        //Serial.println(current_pos);
    }
    else {
        //Serial.println("Invalid position");
    }
}

// acquisition parameters
bool acquisition_state = 0;         // 0 is not ready for acquisition, 1 is ready for acquisition
String params = "";                 // acquisition parameters
String filter_params = "";     // acquisition parameters
String laser_params = "";           // laser parameters
int timeout = 100;                  // camera timeout

void loop()
{   
    if (Serial.available() > 0) {
        String imswitch_command = Serial.readString();
        int length = imswitch_command.length();
        //Serial.print("Imswitch command: ");
        //Serial.println(imswitch_command);
        int run_state = 0;
        if (length == 1) {
            move_to(imswitch_command.toInt());             // if serial read is only one digit it means move the slider to a specific position, NOT scanning
        }
        else if (imswitch_command == "begin" && acquisition_state == 1){             // do the scanning
            //Serial.println("Acquisition started");
            run_state = 1;
            int image_number = 0;
            int stage_number = 0;
            int param_length = params.length();
            int filter_pos[param_length/2];
            int laser_ids[param_length/2];
            //Serial.println("Acquisition parameters:");
            //Serial.println(params);
            for (int i = 0; i < param_length; i++) {
                if (i % 2 == 0) {
                // Even index (0, 2, 4) goes to filter_pos
                    filter_pos[i / 2] = (params.charAt(i) - '0');
                } else {
                // Odd index (1, 3, 5) goes to laser_ids
                    laser_ids[i / 2] = (params.charAt(i) - '0');
                }
            }
            //Serial.println("Filter positions:");
            //for (int i = 0; i < param_length/2; i++) {
                //Serial.println(filter_pos[i]);
            //}
            //Serial.println("Laser IDs:");
            //for (int i = 0; i < param_length/2; i++) {
                //Serial.println(laser_ids[i]);
            //}
            int number_lasers = sizeof(laser_ids) / sizeof(laser_ids[0]);
            delay(1000);                // some time for imswitch to figure stuff out
            while (acquisition_state == 1 && run_state == 1) {
                
                //Serial.println("Acquisition loop");
                for (int laserID = 0; laserID < number_lasers; laserID++) {
                    
                    //Serial.print("Laser ID: ");
                    //Serial.println(laser_ids[laserID]);
                    //Serial.print("Filter position: ");
                    //Serial.println(filter_pos[laserID]);
                    //Serial.println("current pos");
                    //Serial.println(current_pos);
                    if (filter_pos[laserID] == current_pos) {
                        delay(100);  // cam_readout_delay  , should be 1000/30.15 = 33.2 ms, is stopping the acquisition sometimes due to overflow buffer error
                        //Serial.println("already there");
                    }
                    else {
                        move_to(filter_pos[laserID]);
                    }
                    digitalWrite(laser_ids[laserID], HIGH);
                    //Serial.println("Laser triggered");
                    //Serial.println(image_number);
                    digitalWrite(cam_out, HIGH);
                    delay(1);                                           // possibly shorter
                    digitalWrite(cam_out, LOW);
                    if (digitalRead(cam_exp_in) == HIGH) {           // check if camera is exposing micromanager side
                        image_number++;
                        while (digitalRead(cam_exp_in) == HIGH) {     // check if camera is exposing
                            digitalWrite(ledPin, HIGH);                     //TODO add a timeout
                            delay(1);
                        }
                    }
                    else {
                        digitalWrite(laser_ids[laserID], LOW);      // exit the acquisition entirely
                        digitalWrite(ledPin, LOW);
                        digitalWrite(cam_out, LOW);
                        //Serial.println("Camera is not exposing, exiting acquisition");
                        run_state = 0;
                        //Serial.println(stage_number);
                        //Serial.println(image_number);
                        break;
                    }
                    digitalWrite(laser_ids[laserID], LOW);
                    digitalWrite(ledPin, LOW);
                }
                if (run_state == 1) {
                    digitalWrite(stage_sample, HIGH);
                    digitalWrite(stage_camera, HIGH);
                    delay(10);                               // change to 10 241122
                    digitalWrite(stage_sample, LOW);
                    digitalWrite(stage_camera, LOW);
                    //Serial.println("Stage triggered");
                    while (digitalRead(stage_sample_in) == HIGH) {           // check if stage is moving
                        delayMicroseconds(10);
                        //Serial.println("Stage is moving");
                    }
                    delay(100);                // some time for stage to settle, should remove
                    stage_number++;
                    reverseArray(filter_pos, param_length/2);
                    reverseArray(laser_ids, param_length/2);
                }
            }
        }
        else  {
            //Serial.println("Acquisition parameters:");
            params = imswitch_command;
            //Serial.println(params);
            acquisition_state = 1;                          // serial provided the parameters for the acquisition, waiting for "begin" commant to start
        }
    }
}
