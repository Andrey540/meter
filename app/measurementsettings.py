from camerasettings import CameraSettings
from colorsettings import ColorSettings
from configparser import ConfigParser, NoOptionError
from numpy import array, uint8

MAX_CAMERA_WIDTH = 3280
MAX_CAMERA_HEIGHT = 2464

class MeasurementSettings:
    def __init__(self):
        self.cameraSettings = CameraSettings()
        self.colorSettings = ColorSettings()
        self.multiThread = True

        self.tuneMonochromeView = False
        self.showOriginalView = False
        self.tuneColors = False
        self.showVertexValues = False
        self.tuneMonochromeColorsView = False
        self.viewPortWidth = 1024
        self.shapeSliceHeight = 2
        self.resultViewHeight = 0.2

        self.skipStartFramesCount = 0
        self.tresholdValue = 80

        self.cheksCount = 30
        self.confidenceFactor = 0.9
        self.checkTrueValue = 255
        self.__initDefaultSettings()
        self.__initDefaultColorSettings()

    def initFromFile(self, file):
        config = ConfigParser()
        config.read(file)
        resolutionWidth = config.getint("Camera", "ResolutionWidth")
        resolutionHeight = config.getint("Camera", "ResolutionHeight")

        self.cameraSettings.resolution = (resolutionWidth, resolutionHeight)
        self.cameraSettings.satutation = self.__getIntOptionFromConfig(config, "Camera", "Saturation")
        self.cameraSettings.contrast = self.__getIntOptionFromConfig(config, "Camera", "Contrast")
        self.cameraSettings.brightness = self.__getIntOptionFromConfig(config, "Camera", "Brightness")
        self.cameraSettings.hue = self.__getIntOptionFromConfig(config, "Camera", "Hue")
        self.cameraSettings.gain = self.__getIntOptionFromConfig(config, "Camera", "Gain")
        self.cameraSettings.exposure = self.__getIntOptionFromConfig(config, "Camera", "Exposure")
        self.cameraSettings.frameRate = self.__getIntOptionFromConfig(config, "Camera", "FrameRate")

        self.__initDefaultSettings()

        self.viewPortWidth = config.getint("View", "ViewPortWidth")
        self.showOriginalView = config.getboolean("View", "ShowOriginalView")
        self.showVertexValues = config.getboolean("View", "ShowVertexValues")

        self.tuneMonochromeView = config.getboolean("Tune", "TuneMonochromeView")
        self.tuneColors = config.getboolean("Tune", "TuneColors")
        self.tuneMonochromeColorsView = config.getboolean("Tune", "TuneMonochromeColorsView")

        self.multiThread = config.getboolean("Measurement", "MultiThread")
        self.tresholdValue = config.getint("Measurement", "TresholdValue")
        self.cheksCount = config.getint("Measurement", "CheksCount")
        self.confidenceFactor = config.getfloat("Measurement", "ConfidenceFactor")

        self.minMeasurementShapeHeight = int(config.getint("Measurement", "MinMeasurementShapeHeight") / self.resolutionCoeff)
        self.minMeasurementShapeWidth = int(config.getint("Measurement", "MinMeasurementShapeWidth") / self.resolutionCoeff)

        self.minColorShapeHeight = int(config.getint("Measurement", "MinColorShapeHeight") / self.resolutionCoeff)
        self.minColorShapeWidth = int(config.getint("Measurement", "MinColorShapeWidth") / self.resolutionCoeff)

        self.resultColorShapeWidth = int(config.getint("Measurement", "ResultColorShapeWidth") / self.resolutionCoeff)

        self.colorSettings.grayColorFilter = [
            array((
                config.getint("Colors", "MinGrayColorFilterH"),
                config.getint("Colors", "MinGrayColorFilterS"),
                config.getint("Colors", "MinGrayColorFilterV")
            ), uint8),
            array((
                config.getint("Colors", "MaxGrayColorFilterH"),
                config.getint("Colors", "MaxGrayColorFilterS"),
                config.getint("Colors", "MaxGrayColorFilterV")
            ), uint8),
        ]

        self.colorSettings.baseRedColor = (
            config.getint("Colors", "BaseRedColorR"),
            config.getint("Colors", "BaseRedColorG"),
            config.getint("Colors", "BaseRedColorB")
        )
        self.colorSettings.basePurpleColor = (
            config.getint("Colors", "BasePurpleColorR"),
            config.getint("Colors", "BasePurpleColorG"),
            config.getint("Colors", "BasePurpleColorB")
        )
        self.colorSettings.baseGreenColor = (
            config.getint("Colors", "BaseGreenColorR"),
            config.getint("Colors", "BaseGreenColorG"),
            config.getint("Colors", "BaseGreenColorB")
        )
        self.colorSettings.baseCyanColor = (
            config.getint("Colors", "BaseCyanColorR"),
            config.getint("Colors", "BaseCyanColorG"),
            config.getint("Colors", "BaseCyanColorB")
        )
        self.colorSettings.baseBlueColor = (
            config.getint("Colors", "BaseBlueColorR"),
            config.getint("Colors", "BaseBlueColorG"),
            config.getint("Colors", "BaseBlueColorB")
        )
        self.colorSettings.baseYellowColor = (
            config.getint("Colors", "BaseYellowColorR"),
            config.getint("Colors", "BaseYellowColorG"),
            config.getint("Colors", "BaseYellowColorB")
        )

        return;

    def __getIntOptionFromConfig(self, config, section, option):
        try:
            return config.getint(section, option)
        except NoOptionError:
            return None

    def __initDefaultColorSettings(self):
        self.colorSettings.grayColorFilter = [
            array((68, 0, 100), uint8),
            array((198, 96, 255), uint8),
        ]
        self.colorSettings.baseRedColor = (40, 60, 90)
        self.colorSettings.basePurpleColor = (128, 0, 128)
        self.colorSettings.baseGreenColor = (50, 70, 35)
        self.colorSettings.baseCyanColor = (116, 88, 43)
        self.colorSettings.baseBlueColor = (134, 38, 42)
        self.colorSettings.baseYellowColor = (39, 127, 147)

    def __initDefaultSettings(self):
        self.resolutionCoeff = MAX_CAMERA_WIDTH / self.cameraSettings.resolution[0]
        self.minMeasurementShapeHeight = int(300 / self.resolutionCoeff)
        self.minMeasurementShapeWidth = int(20 / self.resolutionCoeff)

        self.minColorShapeHeight = int(150 / self.resolutionCoeff)
        self.minColorShapeWidth = int(150 / self.resolutionCoeff)
        self.groupColorShapeDistance = int(300 / self.resolutionCoeff)
        self.resultColorShapeWidth = int(140 / self.resolutionCoeff)
        
        self.distanceLabelOffsetX = int(250 / self.resolutionCoeff)
        self.distanceLabelOffsetY = int(800 / self.resolutionCoeff)
        self.vertexLabelOffsetY = int(200 / self.resolutionCoeff)

        self.resultLabelOffsetX = int(730 / self.resolutionCoeff)
        self.resultLabelOffsetY = int(280 / self.resolutionCoeff)

        self.lineWidth = int(8 / self.resolutionCoeff)
        self.textSize = 4.0 / self.resolutionCoeff
        self.colorTextSize = 4.0 / self.resolutionCoeff
        self.resultTextSize = 12.0 / self.resolutionCoeff
        self.resultLineWidth = int(16 / self.resolutionCoeff)
        self.checkBottomOffset = int(20 / self.resolutionCoeff)
        return
