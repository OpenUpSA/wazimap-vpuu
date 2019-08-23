FROM postgres:9.4

RUN mkdir /docker-entrypoint-initdb.d/census/
COPY sql/census/ /docker-entrypoint-initdb.d/census
COPY sql/extensions/ /docker-entrypoint-initdb.d/
