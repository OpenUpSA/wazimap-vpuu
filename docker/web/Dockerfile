FROM python:3.6

ENV PYTHONUNBUFFERED 1

ENV WKHTMLTOPDF_VERSION=0.12.4
RUN wget https://github.com/wkhtmltopdf/wkhtmltopdf/releases/download/${WKHTMLTOPDF_VERSION}/wkhtmltox-${WKHTMLTOPDF_VERSION}_linux-generic-amd64.tar.xz && \
    tar xvf wkhtmltox-${WKHTMLTOPDF_VERSION}_linux-generic-amd64.tar.xz && \
    mv wkhtmltox/bin/wkhtmlto* /usr/bin/ && \
    rm -r wkhtmltox wkhtmltox-${WKHTMLTOPDF_VERSION}_linux-generic-amd64.tar.xz


RUN apt update && apt install -y gdal-bin libgdal-dev git locales


ENV CPLUS_INCLUDE_PATH /usr/include/gdal
ENV C_INCLUDE_PATH /usr/include/gdal
ENV LANG C.UTF-8

RUN mkdir /vpuu
WORKDIR /vpuu

COPY . /vpuu

RUN pip install --upgrade setuptools && pip install -r docker-requirements.txt
