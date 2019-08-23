from django.test import TestCase
from django.conf import settings
from wazimap.models import FieldTable, FieldTableRelease, DBTable
from wazimap.models import Geography, Dataset, Release
from dynamic_profile.models import Profile, IndicatorProfile
import psycopg2
from psycopg2 import sql
import csv
import os

WAZI_PROFILE = settings.WAZIMAP["default_profile"]


class ProfileTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        Geography.objects.create(
            geo_level="country", geo_code="ZA", version="2011", name="South Africa"
        )
        Geography.objects.create(
            geo_level="country", geo_code="ZA", version="2016", name="South Africa"
        )

        dataset = Dataset.objects.create(name="Census and Community Survey")

        release_2011 = Release.objects.create(
            name="Census",
            year="2011",
            citation="Statistics South Africa (2011) South African Population Census 2011",
            dataset=dataset,
        )
        release_2016 = Release.objects.create(
            name="Community Survey",
            year="2016",
            citation="Statistics South Africa (2016) South African Population Census 2016",
            dataset=dataset,
        )

        population_db = DBTable.objects.create(name="populationgroup")
        population_2016_db = DBTable.objects.create(name="populationgroup_2016")

        # Add some population data
        population_field_table = FieldTable.objects.create(
            name="POPULATIONGROUP",
            universe="Population",
            dataset=dataset,
            fields=["population group"],
            has_total=True,
        )
        population_field_table_2016 = FieldTable.objects.create(
            name="POPULATIONGROUP_2016",
            universe="Population",
            dataset=dataset,
            fields=["population group"],
            has_total=True,
        )

        FieldTableRelease.objects.create(
            data_table=population_field_table,
            db_table=population_db,
            release=release_2011,
        )
        FieldTableRelease.objects.create(
            data_table=population_field_table,
            db_table=population_2016_db,
            release=release_2016,
        )
        FieldTableRelease.objects.create(
            data_table=population_field_table_2016,
            db_table=population_2016_db,
            release=release_2016,
        )

        population_field_table.description = (
            "population of different race groups for 2011"
        )
        population_field_table.save()

        population_field_table.description_2016 = (
            "population of different race groups for 2016"
        )
        population_field_table_2016.save()

        # Create a profile for the population indicator
        profile = Profile.objects.create(name="Demographics")
        IndicatorProfile(
            profile=profile,
            table_name=population_field_table,
            column_name="population group",
            header="Population",
            summary="People",
            chart_title="Population Group",
            chart_type="histogram",
            order_by=True,
            maximum_value="total",
        )
        # insert the population data.
        # django does not know about the table so have to use this

        connection = psycopg2.connect(
            "postgresql://wazimap_vpuu:wazimap_vpuu@development/test_wazimap_vpuu"
        )
        cursor = connection.cursor()
        pop_csv = os.getcwd() + "/vpuu/tests/populationgroup.csv"
        pop_2016_csv = os.getcwd() + "/vpuu/tests/populationgroup_2016.csv"
        with open(pop_csv, "r") as f:
            reader = csv.DictReader(f)
            query = sql.SQL(
                "INSERT into populationgroup(geo_level,geo_code,geo_version, {}, total) values(%s,%s,%s,%s,%s)"
            )
            for row in reader:
                cursor.execute(
                    query.format(sql.Identifier("population group")),
                    (
                        row["geo_level"],
                        row["geo_code"],
                        row["geo_version"],
                        row["population group"],
                        row["total"],
                    ),
                )
            connection.commit()
        with open(pop_2016_csv, "r") as f:
            reader = csv.DictReader(f)
            query = sql.SQL(
                "INSERT into populationgroup_2016(geo_level,geo_code,geo_version, {}, total) values(%s,%s,%s,%s,%s)"
            )
            for row in reader:
                cursor.execute(
                    query.format(sql.Identifier("population group")),
                    (
                        row["geo_level"],
                        row["geo_code"],
                        row["geo_version"],
                        row["population group"],
                        row["total"],
                    ),
                )
            connection.commit()
        connection.close()

    def test_home_page(self):
        resp = self.client.get("/")
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Discover the story behind the data")

    # def test_geo_country(self):
    #     resp = self.client.get("/profiles/country-ZA-south-africa/?release=2011")
    #     print(resp.context["indicator"])
    #     self.assertEqual(resp.status_code, 200)
    #     self.assertContains(resp, "South Africa")
    #     # self.assertContains(resp, "Population group")  # Chart title
    #     self.assertContains(resp, "51 770 560 people")  # Total population

    def test_geo_country_2016(self):
        resp = self.client.get("/profiles/country-ZA-south-africa/")
        self.assertEqual(resp.status_code, 200)
        print(resp.context["indicator"])
        self.assertContains(resp, "South Africa")
        self.assertContains(resp, "55 653 654 people")  # Total population
        self.assertContains(resp, "Population group")  # Chart title
