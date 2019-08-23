FROM ubuntu:18.04

ENV PYTHONUNBUFFERED 1

RUN apt-get update && apt install -y gdal-bin libgdal-dev
RUN apt install -y python-pip git

ENV CPLUS_INCLUDE_PATH /usr/include/gdal
ENV C_INCLUDE_PATH /usr/include/gdal

RUN mkdir /vpuu
WORKDIR /vpuu

COPY . /vpuu

RUN pip install -r requirements.txt
