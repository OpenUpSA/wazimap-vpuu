import logging
import psycopg2
from psycopg2 import sql
from django.conf import settings

log = logging.getLogger(__name__)


class UploadedDataSet(object):
    def __init__(self, f, field_table):
        self._uploaded_file = f
        self._field_table = field_table

    def insert_data(self):
        """
        Insert data from the uploaded file into the table corresponding to the 
        FieldTable. We assume the file is in the correct format and contains 
        valid values.
        """
        connection = psycopg2.connect(settings.DATABASE_URL)
        cursor = connection.cursor()
        table_name = sql.Identifier(self._field_table.name.lower())
        field_columns = self._field_table.fields
        values_query_segment = ','.join(['%s'] * (len(field_columns) + 4))
        query = sql.SQL("INSERT into {} values(%s)" % values_query_segment)
        for row in self._uploaded_file:
            query_string = query.format(table_name)
            cursor.execute(query_string, row.strip().split(','))
        connection.commit()