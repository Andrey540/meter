#!/usr/bin/python3
from measurementsettings import MeasurementSettings
from meter import Meter
import RPi.GPIO as GPIO
import time
import threading
import os

PIN_NUMBER = 27

GPIO.setmode(GPIO.BCM)

GPIO.setup(PIN_NUMBER, GPIO.IN, pull_up_down = GPIO.PUD_UP)

settings = MeasurementSettings()
settings.initFromFile(os.environ.get('APP_PATH') + "/settings/settings.ini")
meter = Meter(settings)

def runMeasurements(meter):
    meter.startMeasurement()
    return

def measurementsCallback(channel):
    global meter
    if meter.isMeasurementRunning() == True:
        meter.stopMeasurement()
    else:
        thread = threading.Thread(target = runMeasurements, args = (meter, ))
        thread.start()

    return

GPIO.add_event_detect(PIN_NUMBER, GPIO.FALLING, callback = measurementsCallback, bouncetime = 2000)

try:
    while True:
        time.sleep(2)
except KeyboardInterrupt:
    GPIO.cleanup()

GPIO.cleanup()
