FROM ubuntu:18.04

ENV PYTHONUNBUFFERED 1

RUN apt-get update && apt install -y gdal-bin libgdal-dev git python3-pip python3

ENV CPLUS_INCLUDE_PATH /usr/include/gdal
ENV C_INCLUDE_PATH /usr/include/gdal

RUN mkdir /vpuu
WORKDIR /vpuu

COPY . /vpuu

RUN pip3 install -r docker-requirements.txt
