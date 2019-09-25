import logging
import psycopg2
from psycopg2 import sql
from django.conf import settings

log = logging.getLogger(__name__)


class UploadedDataSet(object):
    def __init__(self, f, field_table):
        self._uploaded_file = f
        self._field_table = field_table
    
    def read_file(self):
        with open('uploaded_dataset.csv', 'wb+') as destination:
            for chunk in self._uploaded_file.chunks():
                destination.write(chunk)
    
    def validate(self):
        # Headers: geo_level,geo_code, <field_name>,total,geo_version
        pass

    def create_dataset(self):
        # Headers: geo_level,geo_code, <field_name>,total,geo_version
        connection = psycopg2.connect(settings.DATABASE_URL)
        cursor = connection.cursor()
        q = 'SELECT count(*) from {};'.format(self._field_table.name.lower())
        cursor.execute(q)
        result = cursor.fetchone()
        table_name = sql.Identifier(self._field_table.name.lower())
        # TODO: get multiple field columns
        field_column_name = sql.Identifier(self._field_table.fields[0].lower())
        query = sql.SQL(
            "INSERT into {} values(%s,%s,%s,%s,%s)"
        )
        for row in self._uploaded_file:
            query_string = query.format(table_name, field_column_name)
            cursor.execute(query_string, row.strip().split(','))
        connection.commit()