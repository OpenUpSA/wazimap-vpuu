#!/bin/bash

# Loop through all the tables and extract the specific region to csv.

export PGPASSWORD=wazimap_vpuu

psql -U wazimap_vpuu -h development -t -c "select tablename from pg_tables WHERE tableowner='wazimap_vpuu'"| while read TABLENAME; do
    echo "$TABLENAME"
    psql -U wazimap_vpuu -h development -c "\copy (select * from $TABLENAME where geo_code='ZA') to '/tmp/$TABLENAME.csv' csv header"
    done
