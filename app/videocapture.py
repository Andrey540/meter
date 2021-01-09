import threading
import cv2

class VideoCapture:
    def __init__(self, src, cameraSettings, isAsync):

        self.__src = src
        self.__cameraSettings = cameraSettings
        self.__isAsync = isAsync
        self.__camera = cv2.VideoCapture(self.__src)
        self.__camera.set(3, self.__cameraSettings.resolution[0])
        self.__camera.set(4, self.__cameraSettings.resolution[1])

        if self.__cameraSettings.frameRate != None:
            self.__camera.set(5, self.__cameraSettings.frameRate)
        if self.__cameraSettings.brightness != None:
            self.__camera.set(10, self.__cameraSettings.brightness)
        if self.__cameraSettings.contrast != None:
            self.__camera.set(11, self.__cameraSettings.contrast)
        if self.__cameraSettings.saturation != None:
            self.__camera.set(12, self.__cameraSettings.saturation)
        if self.__cameraSettings.hue != None:
            self.__camera.set(13, self.__cameraSettings.hue)
        if self.__cameraSettings.gain != None:
            self.__camera.set(14, self.__cameraSettings.gain)
        if self.__cameraSettings.exposure != None:
            self.__camera.set(15, self.__cameraSettings.exposure)

        self.__grabbed, self.__frame = self.__camera.read()
        self.__started = False
        self.__readLock = threading.Lock()

    def start(self):
        if self.__started:
            return None
        self.__started = True
        if self.__isAsync:
            self.__thread = threading.Thread(target=self.update, args=())
            self.__thread.start()
        return self;

    def update(self):
        while self.__started:
            grabbed, frame = self.__camera.read()
            with self.__readLock:
                self.__grabbed = grabbed
                self.__frame = frame
                
    def read(self):
        if not self.__isAsync:
            return self.__camera.read()
        with self.__readLock:
            frame = self.__frame.copy()
            grabbed = self.__grabbed
        return grabbed, frame

    def stop(self):
        self.__started = False
        if self.__isAsync:
            self.__thread.join()

    def __exit__(self, execType, execValue, traceback):
        self.__camera.release()
