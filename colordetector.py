from scipy.spatial import distance as dist
from collections import OrderedDict
import numpy as np
import cv2
import enum

class Colors(enum.IntEnum):
   Green = 0
   Red = 1
   Blue = 2
   Yellow = 3
   Cyan = 4
   Purple = 5
   

class ColorDetector:
   def __init__(self, colorSettings):
      self.initColors(colorSettings)

   def detectColor(self, frame, contour):
      # construct a mask for the contour, then compute the
      # average L*a*b* value for the masked region
      mask = np.zeros(frame.shape[:2], dtype="uint8")
      cv2.drawContours(mask, [contour], -1, 255, -1)
      mask = cv2.erode(mask, None, iterations=2)
      mean = cv2.mean(frame, mask=mask)[:3]
      # initialize the minimum distance found thus far
      minDist = (np.inf, None)
      # loop over the known L*a*b* color values
      for (i, color) in enumerate(self.colors):
          # compute the distance between the current L*a*b*
          # color value and the mean of the image
          distance = dist.euclidean(color, mean)
          # if the distance is smaller than the current distance,
          # then update the bookkeeping variable
          if distance < minDist[0]:
              minDist = (distance, i)
          # return the name of the color with the smallest distance    
      return self.colorCodes[minDist[1]]

   def initColors(self, colorSettings):
      colors = OrderedDict()
      colors[Colors.Red] = colorSettings.baseRedColor
      colors[Colors.Purple] = colorSettings.basePurpleColor
      colors[Colors.Green] = colorSettings.baseGreenColor
      colors[Colors.Cyan] = colorSettings.baseCyanColor
      colors[Colors.Blue] = colorSettings.baseBlueColor
      colors[Colors.Yellow] = colorSettings.baseYellowColor

      # allocate memory for the L*a*b* image, then initialize
      # the color names list
      self.colors = np.zeros((len(colors), 1, 3), dtype="uint8")
      self.colorCodes = []
      # loop over the colors dictionary
      for (i, (colorCode, value)) in enumerate(colors.items()):
          self.colors[i] = value
          self.colorCodes.append(colorCode)
