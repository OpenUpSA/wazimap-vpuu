FROM ubuntu:latest

ENV PYTHONUNBUFFERED 1

RUN apt update && apt install -y gdal-bin libgdal-dev git python3-pip locales 

ENV CPLUS_INCLUDE_PATH /usr/include/gdal
ENV C_INCLUDE_PATH /usr/include/gdal
ENV LANG='en_US.UTF-8' LANGUAGE='en_US:en' LC_ALL='en_US.UTF-8'

RUN locale-gen en_US.UTF-8
RUN mkdir /vpuu
WORKDIR /vpuu

COPY . /vpuu

RUN pip3 install -r docker-requirements.txt
