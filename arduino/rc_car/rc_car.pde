#include <Servo.h>

Servo turn;
Servo drive;
Servo cam;

#define CMD_SET_TURN  0
#define CMD_SET_DRIVE 1
#define CMD_SET_CAM   2

void setup()
{
  turn.attach(10);
  drive.attach(9);
  cam.attach(3);
  Serial.begin(9600); //open serial port 9600 b
  turn.write(90);
  drive.write(90);
  cam.write(90);
}

void loop()
{
  while(Serial.available() > 0) {
    int inst = Serial.read();
    if (inst == CMD_SET_TURN || inst == CMD_SET_DRIVE || inst == CMD_SET_CAM)    {
      while (Serial.available() < 1);
      int val = Serial.read();
      if      (inst == CMD_SET_TURN)  turn.write(val);
      else if (inst == CMD_SET_DRIVE) drive.write(val);
      else if (inst == CMD_SET_CAM) cam.write(val);
    }
  }
}

