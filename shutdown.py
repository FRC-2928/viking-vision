#!/usr/bin/env python2

import os
import time
import RPi.GPIO as GPIO

switchPin = 20
powerPin = 26
GPIO.setmode(GPIO.BCM)
GPIO.setup(powerPin, GPIO.OUT)
GPIO.setup(switchPin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

GPIO.output(powerPin, GPIO.HIGH)
while True:
    if(GPIO.input(switchPin)):
        os.system("sudo shutdown now")
    time.sleep(0.125)
GPIO.cleanup()
