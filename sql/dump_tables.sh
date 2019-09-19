#!/bin/bash

export PGPASSWORD=wazimap_vpuu

for t in `ls census/[a-z]*.sql`
do
    pg_dump "postgres://wazimap_vpuu@development/wazimap_vpuu" \
        -O -c --if-exists -t $(basename $t .sql) \
      | egrep -v "(idle_in_transaction_session_timeout|row_security)" \
      > census/$(basename $t .sql).sql
done
