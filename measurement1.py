#!/usr/bin/python3
from measurementsettings import MeasurementSettings
from meter import Meter

settings = MeasurementSettings()
settings.initFromFile("/home/projects/settings/settings.ini")
meter = Meter(settings)
meter.startMeasurement()
