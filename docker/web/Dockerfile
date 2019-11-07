FROM python:3.6

ENV PYTHONUNBUFFERED 1

RUN apt update && apt install -y gdal-bin libgdal-dev git locales 

ENV CPLUS_INCLUDE_PATH /usr/include/gdal 
ENV C_INCLUDE_PATH /usr/include/gdal
ENV LANG C.UTF-8

RUN mkdir /vpuu
WORKDIR /vpuu

COPY . /vpuu

RUN pip install --upgrade setuptools && pip install -r docker-requirements.txt
