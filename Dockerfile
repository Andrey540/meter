FROM jjanzic/docker-python3-opencv:contrib-opencv-4.0.1

RUN pip install --upgrade pip && pip install scipy && pip install imutils && pip install configparser && pip install opencv-python

ENV APP_PATH "/usr/local/app"
COPY app /usr/local/app/