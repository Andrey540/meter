#!/usr/bin/python3
from measurementsettings import MeasurementSettings
from meter import Meter
import os

settings = MeasurementSettings()
settings.initFromFile(os.environ.get('APP_PATH') + "/settings/settings.ini")
meter = Meter(settings)
meter.startMeasurement()
