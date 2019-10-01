import logging
import psycopg2
from psycopg2 import sql
from django.conf import settings

log = logging.getLogger(__name__)


class UploadedDataSet(object):
    """
    Class to create and process datasets that were uploaded from the admin site.
    """
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

        table_name = self._field_table.name.lower()

        cursor.copy_from(self._uploaded_file, table_name, sep=',')

        connection.commit()
