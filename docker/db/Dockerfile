FROM postgres:9.4

RUN apt update && apt install -y unzip

COPY sql/census.zip /docker-entrypoint-initdb.d/
COPY sql/extensions/ /docker-entrypoint-initdb.d/
RUN mkdir /docker-entrypoint-initdb.d/census
RUN chmod 777 -R /docker-entrypoint-initdb.d/census
