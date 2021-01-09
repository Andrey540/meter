from numpy import mean, var, std, array, uint8, int32, inf
from shapedetector import ShapeDetector
from colordetector import ColorDetector, Colors
from camerasettings import CameraSettings
from measurementsettings import MeasurementSettings
from videocapture import VideoCapture
import time
import imutils
import cv2

MONOCHROME_SETTINGS_WINDOW = 'monochromeSettings'
MONOCHROME_COLORS_SETTINGS_WINDOW = 'monochromeColorsSettings'
COLORS_SETTINGS_WINDOW1 = 'colorsSettings1'
COLORS_SETTINGS_WINDOW2 = 'colorsSettings2'

class Meter:
    def __init__(self, settings):
        self.__settings = settings
        self.__isRunning = False
        self.__frame = None
        self.__monochromeFrame = None
        self.__originalFrame = None
        self.__vertexesCache = None
        self.__camera = VideoCapture(0, self.__settings.cameraSettings, self.__settings.multiThread)
        self.__colorNames = self.__getColorNames()

    def nothing(*arg):
        pass
    
    def startMeasurement(self):
        if self.isMeasurementRunning() == True:
            return

        self.__isRunning = True
        self.__camera.start()

        contourIndex = None
        colorValue = None
        colorCoordinareX = None
        pointX = 0
        count = 0
        colorDetector = ColorDetector(self.__settings.colorSettings)

        self.__showSettingsWindow()

        while True:
            ret, frame = self.__camera.read()
            if not ret:
                break

            pointX = int(frame.shape[1] / 2)
            self.__vertexesCache = {}
    
            originalFrame = frame          
            self.__originalFrame = originalFrame
            self.__monochromeFrame = self.__makeFrameMonochrome(self.__originalFrame)
            self.__monochromeFrame = self.__drawRectangle(self.__monochromeFrame)
            self.__monochromeFrame = self.__invertColors(self.__monochromeFrame)

            colorDetector.initColors(self.__settings.colorSettings)
            colorLabels = self.__getColoredLabels(colorDetector, self.__originalFrame, originalFrame)
            groupedColorLabels = self.__groupColorLabels(colorLabels)
            colorValues = self.__calculateColorValues(groupedColorLabels)

            contours = self.__findContours(self.__monochromeFrame)
            image = originalFrame
            image = self.__drawContours(originalFrame, contours)
            image = self.__drawCenter(image)
            self.__frame = image


            if count < self.__settings.skipStartFramesCount:
                count = count + 1
            else:
                contourIndex = self.__findNearestContour(contours, pointX)
                colorCoordinareX, colorValue = self.__findNearestColorValue(colorValues, pointX)

            if (contourIndex != None):
                contourDistance = self.__getDistanceBetweenPointAndContour(contours[contourIndex], pointX)

                contourVertex = self.__findVertex(contours[contourIndex])
                sign = 1 if (contourVertex[0] < pointX) else -1
                contourDistanceSign = 1 if (contourVertex[0] < colorCoordinareX) else -1
                colorValue = colorValue if (contourVertex[0] < colorCoordinareX) else colorValue + 1

                otherContourIndex = contourIndex + 1 * sign
                if (otherContourIndex < len(contours)):
                    ontherVertex = self.__findVertex(contours[otherContourIndex])
                    distanceBetweenVertexes = (ontherVertex[0] - contourVertex[0]) * sign * -1
                    if (distanceBetweenVertexes != 0):
                        distance = colorValue + (contourDistance / distanceBetweenVertexes)
                        image = self.__printAbsoluteSize(image, format(round(distance, 3), '.3f'))

            image = self.__frame

            self.__showFrame(image, "frame")
            if self.__settings.tuneMonochromeView:
                self.__showFrame(self.__monochromeFrame, "monochrome")
            if self.__settings.showOriginalView:
                self.__showFrame(self.__originalFrame, "original")

            if self.isMeasurementRunning() == False:
                cv2.destroyAllWindows()
                break

        return

    def isMeasurementRunning(self):
        return self.__isRunning
    
    def stopMeasurement(self):
        self.__isRunning = False
        self.__camera.stop()
        return

    def __getColorNames(self):
        colorNames = {}
        colorNames[Colors.Red] = "red"
        colorNames[Colors.Purple] = "purple"
        colorNames[Colors.Green] = "green"
        colorNames[Colors.Cyan] = "cyan"
        colorNames[Colors.Blue] = "blue"
        colorNames[Colors.Yellow] = "yellow"
        return colorNames

    def __getColoredLabels(self, colorDetector, frame, image):
        colorLabels = []
        colorContours = self.__findColorContours(frame)
        for contour in colorContours:
            # compute the center of the contour, then detect the name of the
            # shape using only the contour
            M = cv2.moments(contour)
            cX = int((M["m10"] / M["m00"]))
            cY = int((M["m01"] / M["m00"]))
            truncedContour = self.__createRectContourByCenter(cX, cY)

            colorCode = colorDetector.detectColor(frame, truncedContour)
            colorLabels.append({"colorCode": colorCode, "coordinates": {"x": cX, "y": cY}})
            if self.__settings.tuneColors:
                truncedContour = truncedContour.astype("float")
                truncedContour = truncedContour.astype("int")
                colorText = self.__colorNames[colorCode]
                
                cv2.drawContours(image, [truncedContour], -1, (0, 255, 0), self.__settings.lineWidth)
                cv2.putText(image, colorText, (cX, cY), cv2.FONT_HERSHEY_SIMPLEX, self.__settings.colorTextSize, (255, 255, 255), self.__settings.lineWidth)

        return colorLabels

    def __groupColorLabels(self, colorLabels):
        result = {}
        for (i, colorLabel) in enumerate(colorLabels):
            nearestCoordinate = None
            for i, (coordinate, values) in enumerate(result.items()):
                if abs(coordinate - colorLabel["coordinates"]["x"]) < self.__settings.groupColorShapeDistance:
                    nearestCoordinate = coordinate
            if nearestCoordinate == None:
                result[colorLabel["coordinates"]["x"]] = [colorLabel]
            else:
                result[nearestCoordinate].append(colorLabel)
                
        for i, (coordinate, values) in enumerate(result.items()):
            values.sort(reverse=False, key=lambda item: item["coordinates"]["y"])

        return result

    def __calculateColorValues(self, colorLabels):
        result = {}
        for i, (coordinate, colorLabels) in enumerate(colorLabels.items()):
            value = 0;
            for (i, colorLabel) in enumerate(colorLabels):
                if i > 2:
                    break
                colorValue = int(colorLabel["colorCode"])
                value = (value * 10) + colorValue

            result[coordinate] = int(str(value), 6)

        return result
                    
    def __createRectContourByCenter(self, cX, cY):
        x1 = cX - int(self.__settings.resultColorShapeWidth / 2)
        x2 = cX + int(self.__settings.resultColorShapeWidth / 2)
        y1 = cY - int(self.__settings.resultColorShapeWidth / 2)
        y2 = cY + int(self.__settings.resultColorShapeWidth / 2)

        points = []
        for i in range(self.__settings.resultColorShapeWidth):
            points.append([x1 + i, y1])
        for i in range(self.__settings.resultColorShapeWidth):
            points.append([x2, y1 + i])
        for i in range(self.__settings.resultColorShapeWidth):
            points.append([x2 - i, y2])
        for i in range(self.__settings.resultColorShapeWidth):
            points.append([x1, y2 - i])

        return array(points).reshape((-1, 1, 2)).astype(int32)

    def __updateSettingsValueFunc(self, fieldName, value):
        setattr(self.__settings, fieldName, value)

    def __updateColorFilterFunc(self, field, arrIndex, index, value):
        field[arrIndex][index] = value

    def __updateColorFunc(self, fieldName, index, value):
        currentColor = getattr(self.__settings.colorSettings, fieldName)
        values = list(currentColor)
        values[index] = value
        newColor = tuple(values)
        setattr(self.__settings.colorSettings, fieldName, newColor)

    def __showSettingsWindow(self):
        nothing = lambda *arg: None

        if self.__settings.tuneMonochromeView:
            cv2.namedWindow(MONOCHROME_SETTINGS_WINDOW)
            cv2.createTrackbar('TresholdValue', MONOCHROME_SETTINGS_WINDOW, 0, 255, lambda value: self.__updateSettingsValueFunc('tresholdValue', value))
            cv2.setTrackbarPos("TresholdValue", MONOCHROME_SETTINGS_WINDOW, self.__settings.tresholdValue)

        if self.__settings.tuneMonochromeColorsView:
            cv2.namedWindow(MONOCHROME_COLORS_SETTINGS_WINDOW)

            cv2.createTrackbar('MinGrayH', MONOCHROME_COLORS_SETTINGS_WINDOW, 0, 255, lambda value: self.__updateColorFilterFunc(self.__settings.colorSettings.grayColorFilter, 0 ,0, value))
            cv2.createTrackbar('MinGrayS', MONOCHROME_COLORS_SETTINGS_WINDOW, 0, 255, lambda value: self.__updateColorFilterFunc(self.__settings.colorSettings.grayColorFilter, 0 ,1, value))
            cv2.createTrackbar('MinGrayV', MONOCHROME_COLORS_SETTINGS_WINDOW, 0, 255, lambda value: self.__updateColorFilterFunc(self.__settings.colorSettings.grayColorFilter, 0 ,2, value))
            cv2.createTrackbar('MaxGrayH', MONOCHROME_COLORS_SETTINGS_WINDOW, 0, 255, lambda value: self.__updateColorFilterFunc(self.__settings.colorSettings.grayColorFilter, 1 ,0, value))
            cv2.createTrackbar('MaxGrayS', MONOCHROME_COLORS_SETTINGS_WINDOW, 0, 255, lambda value: self.__updateColorFilterFunc(self.__settings.colorSettings.grayColorFilter, 1 ,1, value))
            cv2.createTrackbar('MaxGrayV', MONOCHROME_COLORS_SETTINGS_WINDOW, 0, 255, lambda value: self.__updateColorFilterFunc(self.__settings.colorSettings.grayColorFilter, 1 ,2, value))

            cv2.setTrackbarPos("MinGrayH", MONOCHROME_COLORS_SETTINGS_WINDOW, self.__settings.colorSettings.grayColorFilter[0][0])
            cv2.setTrackbarPos("MinGrayS", MONOCHROME_COLORS_SETTINGS_WINDOW, self.__settings.colorSettings.grayColorFilter[0][1])
            cv2.setTrackbarPos("MinGrayV", MONOCHROME_COLORS_SETTINGS_WINDOW, self.__settings.colorSettings.grayColorFilter[0][2])
            cv2.setTrackbarPos("MaxGrayH", MONOCHROME_COLORS_SETTINGS_WINDOW, self.__settings.colorSettings.grayColorFilter[1][0])
            cv2.setTrackbarPos("MaxGrayS", MONOCHROME_COLORS_SETTINGS_WINDOW, self.__settings.colorSettings.grayColorFilter[1][1])
            cv2.setTrackbarPos("MaxGrayV", MONOCHROME_COLORS_SETTINGS_WINDOW, self.__settings.colorSettings.grayColorFilter[1][2])

        if self.__settings.tuneColors:
            cv2.namedWindow(COLORS_SETTINGS_WINDOW1)
            cv2.namedWindow(COLORS_SETTINGS_WINDOW2)

            cv2.createTrackbar('RedR', COLORS_SETTINGS_WINDOW1, 0, 255, lambda value: self.__updateColorFunc('baseRedColor', 0, value))
            cv2.createTrackbar('RedG', COLORS_SETTINGS_WINDOW1, 0, 255, lambda value: self.__updateColorFunc('baseRedColor', 1, value))
            cv2.createTrackbar('RedB', COLORS_SETTINGS_WINDOW1, 0, 255, lambda value: self.__updateColorFunc('baseRedColor', 2, value))

            cv2.createTrackbar('PurpleR', COLORS_SETTINGS_WINDOW1, 0, 255, lambda value: self.__updateColorFunc('basePurpleColor', 0, value))
            cv2.createTrackbar('PurpleG', COLORS_SETTINGS_WINDOW1, 0, 255, lambda value: self.__updateColorFunc('basePurpleColor', 1, value))
            cv2.createTrackbar('PurpleB', COLORS_SETTINGS_WINDOW1, 0, 255, lambda value: self.__updateColorFunc('basePurpleColor', 2, value))

            cv2.createTrackbar('GreenR', COLORS_SETTINGS_WINDOW1, 0, 255, lambda value: self.__updateColorFunc('baseGreenColor', 0, value))
            cv2.createTrackbar('GreenG', COLORS_SETTINGS_WINDOW1, 0, 255, lambda value: self.__updateColorFunc('baseGreenColor', 1, value))
            cv2.createTrackbar('GreenB', COLORS_SETTINGS_WINDOW1, 0, 255, lambda value: self.__updateColorFunc('baseGreenColor', 2, value))

            cv2.createTrackbar('CyanR', COLORS_SETTINGS_WINDOW2, 0, 255, lambda value: self.__updateColorFunc('baseCyanColor', 0, value))
            cv2.createTrackbar('CyanG', COLORS_SETTINGS_WINDOW2, 0, 255, lambda value: self.__updateColorFunc('baseCyanColor', 1, value))
            cv2.createTrackbar('CyanB', COLORS_SETTINGS_WINDOW2, 0, 255, lambda value: self.__updateColorFunc('baseCyanColor', 2, value))

            cv2.createTrackbar('BlueR', COLORS_SETTINGS_WINDOW2, 0, 255, lambda value: self.__updateColorFunc('baseBlueColor', 0, value))
            cv2.createTrackbar('BlueG', COLORS_SETTINGS_WINDOW2, 0, 255, lambda value: self.__updateColorFunc('baseBlueColor', 1, value))
            cv2.createTrackbar('BlueB', COLORS_SETTINGS_WINDOW2, 0, 255, lambda value: self.__updateColorFunc('baseBlueColor', 2, value))

            cv2.createTrackbar('YellowR', COLORS_SETTINGS_WINDOW2, 0, 255, lambda value: self.__updateColorFunc('baseYellowColor', 0, value))
            cv2.createTrackbar('YellowG', COLORS_SETTINGS_WINDOW2, 0, 255, lambda value: self.__updateColorFunc('baseYellowColor', 1, value))
            cv2.createTrackbar('YellowB', COLORS_SETTINGS_WINDOW2, 0, 255, lambda value: self.__updateColorFunc('baseYellowColor', 2, value))
            
            cv2.setTrackbarPos("RedR", COLORS_SETTINGS_WINDOW1, self.__settings.colorSettings.baseRedColor[0])
            cv2.setTrackbarPos("RedG", COLORS_SETTINGS_WINDOW1, self.__settings.colorSettings.baseRedColor[1])
            cv2.setTrackbarPos("RedB", COLORS_SETTINGS_WINDOW1, self.__settings.colorSettings.baseRedColor[2])

            cv2.setTrackbarPos("PurpleR", COLORS_SETTINGS_WINDOW1, self.__settings.colorSettings.basePurpleColor[0])
            cv2.setTrackbarPos("PurpleG", COLORS_SETTINGS_WINDOW1, self.__settings.colorSettings.basePurpleColor[1])
            cv2.setTrackbarPos("PurpleB", COLORS_SETTINGS_WINDOW1, self.__settings.colorSettings.basePurpleColor[2])

            cv2.setTrackbarPos("GreenR", COLORS_SETTINGS_WINDOW1, self.__settings.colorSettings.baseGreenColor[0])
            cv2.setTrackbarPos("GreenG", COLORS_SETTINGS_WINDOW1, self.__settings.colorSettings.baseGreenColor[1])
            cv2.setTrackbarPos("GreenB", COLORS_SETTINGS_WINDOW1, self.__settings.colorSettings.baseGreenColor[2])

            cv2.setTrackbarPos("CyanR", COLORS_SETTINGS_WINDOW2, self.__settings.colorSettings.baseCyanColor[0])
            cv2.setTrackbarPos("CyanG", COLORS_SETTINGS_WINDOW2, self.__settings.colorSettings.baseCyanColor[1])
            cv2.setTrackbarPos("CyanB", COLORS_SETTINGS_WINDOW2, self.__settings.colorSettings.baseCyanColor[2])

            cv2.setTrackbarPos("BlueR", COLORS_SETTINGS_WINDOW2, self.__settings.colorSettings.baseBlueColor[0])
            cv2.setTrackbarPos("BlueG", COLORS_SETTINGS_WINDOW2, self.__settings.colorSettings.baseBlueColor[1])
            cv2.setTrackbarPos("BlueB", COLORS_SETTINGS_WINDOW2, self.__settings.colorSettings.baseBlueColor[2])

            cv2.setTrackbarPos("YellowR", COLORS_SETTINGS_WINDOW2, self.__settings.colorSettings.baseYellowColor[0])
            cv2.setTrackbarPos("YellowG", COLORS_SETTINGS_WINDOW2, self.__settings.colorSettings.baseYellowColor[1])
            cv2.setTrackbarPos("YellowB", COLORS_SETTINGS_WINDOW2, self.__settings.colorSettings.baseYellowColor[2])
            
        return
    
    def __showFrame(self, frame, name):
        image = imutils.resize(frame, width = self.__settings.viewPortWidth)
        cv2.imshow(name, image)
        cv2.waitKey(1)
        return

    def __drawRectangle(self, frame):
        frameHeight = frame.shape[0]
        frameWidth = frame.shape[1]

        rectangleHeight = self.__settings.shapeSliceHeight
        rectangleWidth = frameWidth
        rectangleTop = frameHeight - rectangleHeight
    
        return cv2.rectangle(frame, (0, rectangleTop), (rectangleWidth, frameHeight), (255, 255, 0), rectangleHeight)

    def __invertColors(self, frame):
        return ~frame

    def __makeFrameMonochrome(self, frame):   
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        return cv2.threshold(blurred, self.__settings.tresholdValue, 255, cv2.THRESH_BINARY)[1]

    def __findColorContours(self, frame):
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV )

        h_min = self.__settings.colorSettings.grayColorFilter[0]
        h_max = self.__settings.colorSettings.grayColorFilter[1]

        # накладываем фильтр на кадр в модели HSV
        monochromeFrame = cv2.inRange(hsv, h_min, h_max)
        monochromeFrame = self.__invertColors(monochromeFrame)

        if self.__settings.tuneMonochromeColorsView:
            self.__showFrame(monochromeFrame, "monochromeColors")

        cnts = cv2.findContours(monochromeFrame, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        contours = imutils.grab_contours(cnts)
        shapeDetector = ShapeDetector()

        contours = list(filter(lambda item: shapeDetector.isShape(item, self.__settings.minColorShapeHeight, self.__settings.minColorShapeWidth), contours))
        contours.sort(key = lambda item: item[0][0][0])
        return contours

    def __findContours(self, monochromeFrame):
        cnts = cv2.findContours(monochromeFrame.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        contours = imutils.grab_contours(cnts)
        shapeDetector = ShapeDetector()
        
        contours = list(filter(lambda item: shapeDetector.isShape(item, self.__settings.minMeasurementShapeHeight, self.__settings.minMeasurementShapeWidth), contours))
        contours.sort(key = lambda item: item[0][0][0])
        return contours

    def __drawContour(self, frame, contour):       
        contour = contour.astype("float")
        contour = contour.astype("int")
        result = cv2.drawContours(frame, [contour], -1, (0, 255, 0), 2)

        return result

    def __drawCenter(self, frame):
        frameHeight = frame.shape[0]
        frameWidth = frame.shape[1]
        cX = int(frameWidth / 2)
        return cv2.line(frame, (cX, 0), (cX, frameHeight), (0, 255, 0), self.__settings.lineWidth)

    def __drawText(self, frame, contour, text):
        moment = cv2.moments(contour)

        coefficient = 1 if (moment["m00"] == 0) else moment["m00"]
        cX = int(moment["m10"] / coefficient)
        cY = int(moment["m01"] / coefficient)

        return cv2.putText(frame, text, (cX, cY), cv2.FONT_HERSHEY_SIMPLEX, self.__settings.textSize, (255, 255, 255), self.__settings.lineWidth)

    def __findFirsObjecttLine(self, contour):
        (x, y, w, h) = cv2.boundingRect(contour)
        y = y - self.__settings.checkBottomOffset
        h = h - self.__settings.checkBottomOffset

        if (x in self.__vertexesCache):
            return self.__vertexesCache[x]

        height = h if (self.__settings.cheksCount == -1) else self.__settings.cheksCount
        for i in range(w):
            pointX = x + i - 1
            counter = 0
            for j in range(height):
                pointY = y + h - j
                point = self.__monochromeFrame[pointY][pointX]
                if point == self.__settings.checkTrueValue:
                    counter = counter + 1
                if counter >= height * self.__settings.confidenceFactor:
                    self.__vertexesCache[x] = (pointX, y + h)
                    return self.__vertexesCache[x]
        
        return tuple(contour[contour[:, :, 1].argmin()][0])
    
    def __findVertex(self, contour):
        pointsX = []
        top = inf
        for pointArr in contour:
            point = pointArr[0]
            if top == point[1]:
                pointsX.append(point[0])
                
            if top > point[1]:
                top = point[1]
                pointsX = []
                pointsX.append(point[0])

        coordinateX = 0;
        for pointX in pointsX:
            coordinateX += pointX

        coordinateX = coordinateX / len(pointsX)
        return [coordinateX, top]

    def __findVertexes(self, contours):
        result = []
        for contour in contours:
            result.append(self.__findVertex(contour))

        return sorted(result, key = lambda item: item[0])

    def __getDistanceBetweenPointAndContour(self, contour, pointX):
        vertex = self.__findVertex(contour)
        return vertex[0] - pointX

    def __findNearestContour(self, contours, pointX):
        result = None
        minDistance = inf
        for i in range(len(contours)):
            distance = abs(self.__getDistanceBetweenPointAndContour(contours[i], pointX))
            if distance < minDistance:
                minDistance = distance
                result = i
            
        return result

    def __findNearestColorValue(self, colorLabels, pointX):
        nearestCoordinate = None
        minDistance = inf

        for i, (coordinate, colorValue) in enumerate(colorLabels.items()):
            value = 0;
            distance = abs(coordinate - pointX)
            if distance < minDistance:
                minDistance = distance
                nearestCoordinate = coordinate
            
        if nearestCoordinate == None:
            return 0, 0

        return nearestCoordinate, colorLabels[nearestCoordinate] 
    
    def __drawVertexesLabes(self, frame, vertexes):
        frameHeight = frame.shape[0]
        frameWidth = frame.shape[1]

        for vertex in vertexes:
            cX = int(vertex[0] - self.__settings.distanceLabelOffsetX)
            cY = int(self.__settings.vertexLabelOffsetY)
            text = str(format(round(vertex[0], 1), '.1f'))
            cv2.putText(frame, text, (cX, cY), cv2.FONT_HERSHEY_SIMPLEX, self.__settings.textSize, (255, 255, 255), self.__settings.lineWidth)
        
        for i in range(len(vertexes) - 1):
            vertex = vertexes[i]
            nextVertex = vertexes[i + 1]
            distance = nextVertex[0] - vertex[0]
            text = str(format(round(distance, 1), '.1f'))
            cX = int((nextVertex[0] + vertex[0]) / 2 - self.__settings.distanceLabelOffsetX)
            cY = int(frameHeight - self.__settings.distanceLabelOffsetY)

            cv2.putText(frame, text, (cX, cY), cv2.FONT_HERSHEY_SIMPLEX, self.__settings.textSize, (255, 255, 255), self.__settings.lineWidth)

        return frame

    def __drawContours(self, originalFrame, contours):
        shapeDetector = ShapeDetector()
        result = originalFrame.copy()

      #  for contour in contours:
      #      shape = shapeDetector.detect(contour)        
      #      result = self.__drawContour(result, contour)
      #      result = self.__drawText(result, contour, shape)

        vertexes = self.__findVertexes(contours)

        if self.__settings.showVertexValues:
            result = self.__drawVertexesLabes(result, vertexes)

        frameHeight = result.shape[0]
        for vertex in vertexes:
            x = int(vertex[0])
            result = cv2.line(result, (x, 0), (x, frameHeight), (0, 0, 255), self.__settings.lineWidth)

        return result

    def __printAbsoluteSize(self, frame, size):
        frameHeight = frame.shape[0]
        frameWidth = frame.shape[1]

        rectangleHeight = int(self.__settings.resultViewHeight * frameHeight)
        rectangleWidth = frameWidth
        rectengleTop = frameHeight - rectangleHeight
    
        frame = cv2.rectangle(frame, (0, rectengleTop), (rectangleWidth, frameHeight), (0, 0, 0), rectangleHeight)

        cX = int(frameWidth / 2 - self.__settings.resultLabelOffsetX)
        cY = rectengleTop + self.__settings.resultLabelOffsetY
    
        return cv2.putText(frame, str(size), (cX, cY), cv2.FONT_HERSHEY_SIMPLEX, self.__settings.resultTextSize, (255, 255, 255), self.__settings.resultLineWidth)

    def __exit__(self, execType, execValue, traceback):
        self.__camera.stop()
