FROM jjanzic/docker-python3-opencv:contrib-opencv-4.0.1

RUN pip install --upgrade pip && pip install scipy && pip install imutils && pip install configparser && pip install opencv-python

ARG APP_PATH=/usr/local/app
ARG CMD_PATH=${APP_PATH}/cmd.sh

ENV APP_PATH $APP_PATH
COPY app $APP_PATH/

CMD python $APP_PATH/measurement.py