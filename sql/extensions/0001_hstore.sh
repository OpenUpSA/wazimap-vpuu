#!/bin/bash
set -e

psql --username "$POSTGRES_USER" <<-EOSQL
	create extension hstore;
EOSQL

cd /docker-entrypoint-initdb.d/

cat census/*.sql | psql -U postgres -d postgres
