import csv
from collections import defaultdict

from django.core.management.base import BaseCommand, CommandError

import logging

logging.basicConfig()
logging.getLogger('sqlalchemy.engine').setLevel(logging.WARN)


"""
This is a helper script that reads in a structured CSV file with
column names that match the database columns to be created
and ensures the field values add to 100%, and writes the results to a new csv file.
"""


class Command(BaseCommand):
    help = ("Reads a structured CSV file. " +
            "Ensures that the field values add to 100%%" +
            "and writes the results to a new csv file.")

    def add_arguments(self, parser):
        parser.add_argument(
            '--input_file',
            action='store',
            dest='input_file',
            help='The file path to the CSV to check'
        )
        parser.add_argument(
            '--output_file',
            action='store',
            dest='output_file',
            help='The file to write the results to'
        )
        parser.add_argument(
            '--geo_version',
            action='store',
            dest='geo_version',
            default='2011',
            help='The the value for the geo_version column for this data. Default: 2011'
        )

    def debug(self, msg):
        if self.verbosity >= 2:
            self.stdout.write(str(msg))

    def handle(self, *args, **options):
        self.input = options['input_file']
        self.output = options['output_file']
        self.geo_version = options['geo_version']

        with open(self.input) as read_csv:
            self.reader = csv.DictReader(read_csv, delimiter=",")

            # Fields excluding geo_level, geo_code and total
            excl_fields = ['geo_level', 'geo_code', 'geo_version', 'total']
            self.fields = [f for f in self.reader.fieldnames if f not in excl_fields]

            final_field = self.fields[-1]
            self.final_field_values = set()
            for row in self.reader:
                self.final_field_values.add(row[final_field])


        with open(self.input) as read_csv:
            with open(self.output, 'wb') as write_csv:
                self.reader = csv.DictReader(read_csv, delimiter=",")

                fieldnames = self.reader.fieldnames
                if not 'geo_version' in fieldnames:
                    fieldnames.append('geo_version')

                self.writer = csv.DictWriter(write_csv, fieldnames=fieldnames)
                self.writer.writeheader()

                self.check_values()

    def check_values(self):
        totals = defaultdict(float)

        count = 0
        for row in self.reader:
            count += 1
            if row['total'] == 'no data' or not row['total']:
                row['total'] = None
            else:
                row['total'] = float(row['total'])

            geo = row['geo_level'], row['geo_code']
            field_values = tuple(row[field] for field in self.fields[:-1])
            key = (geo + field_values)

            if row['total']:
                totals[key] += row['total']

                if count % len(self.final_field_values) == 0:
                    if totals[key] != 100:
                        diff = totals[key] - 100
                        row['total'] = round(row['total'] - diff, 1)

            if not row['geo_version']:
                row['geo_version'] = self.geo_version

            self.writer.writerow(row)
