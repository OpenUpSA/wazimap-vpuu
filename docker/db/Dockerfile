FROM postgres:9.4

COPY sql/census.zip /docker-entrypoint-initdb.d/
COPY sql/extensions/ /docker-entrypoint-initdb.d/
