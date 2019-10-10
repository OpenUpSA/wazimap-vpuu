from dynamic_profile.utils import BuildIndicator, enhance_api_data
from wazimap.data.tables import get_datatable
from wazimap.data.utils import (
    calculate_median,
    dataset_context,
    get_stat_data,
    group_remainder,
)
from wazimap.models.data import DataNotFound
from wazimap.geo import geo_data
import pdb


class VpuuIndicator(BuildIndicator):
    """
    Add some custom changes for vpuu.
    """

    def __init__(self, *args, **kwargs):
        super(VpuuIndicator, self).__init__(*args, **kwargs)
        self.load_elections()

    def load_elections(self):
        if self.profile.profile.name == "Elections":
            self.election_dates = {
                "National 2014": {
                    "year": "2014",
                    "turnout": "VOTER_TURNOUT_NATIONAL_2014",
                    "geo_version": "2011",
                },
                "Provincial 2014": {
                    "year": "2014",
                    "turnout": "VOTER_TURNOUT_PROVINCIAL_2014",
                    "geo_version": "2011",
                },
                "Municipal 2016": {
                    "year": "2016",
                    "turnout": "VOTER_TURNOUT_MUNICIPAL_2016",
                    "geo_version": "2016",
                },
                "Municipal 2011": {
                    "year": "2011",
                    "turnout": "VOTER_TURNOUT_MUNICIPAL_2011",
                    "geo_version": "2011",
                },
            }

    def elections(self):
        with dataset_context(year=self.election_dates[self.profile.title]["year"]):
            current_version = self.geo.version
            self.geo.version = self.election_dates[self.profile.title]["geo_version"]
            try:
                party_data, total_valid_votes = get_stat_data(
                    ["party"],
                    self.geo,
                    self.session,
                    table_universe=self.profile.universe,
                    table_dataset=self.profile.dataset,
                    exclude_zero=self.profile.exclude_zero,
                    percent=self.profile.percent,
                    recode=self.profile.recode,
                    key_order=self.profile.key_order,
                    exclude=self.profile.exclude,
                    order_by=self.profile.order_by,
                )
                group_remainder(party_data, self.profile.group_remainder)
                self.geo.version = current_version
                party_data = enhance_api_data(party_data)
                return {"stat_values": party_data, "total": total_valid_votes}
            except DataNotFound as error:
                print(error)
                self.geo.version = current_version
                return {}

    def election_turnout(self):
        """
        Get the number of registred voters
        """
        current_version = self.geo.version
        self.geo.version = self.election_dates[self.profile.title]["geo_version"]
        comparative_geos = geo_data.get_comparative_geos(self.geo)

        table = get_datatable(self.election_dates[self.profile.title]["turnout"])
        results = table.get_stat_data(
            self.geo,
            "registered_voters",
            percent=False,
            year=self.election_dates[self.profile.title]["year"],
        )[0]["registered_voters"]

        for comp_geo in comparative_geos:
            comp_results = table.get_stat_data(
                comp_geo,
                "registered_voters",
                percent=False,
                year=self.election_dates[self.profile.title]["year"],
            )[0]["registered_voters"]
            results["values"][comp_geo.geo_level] = comp_results["values"]["this"]

        self.geo.version = current_version
        return results

    def extra_headers(self):
        current_version = self.geo.version
        self.geo.version = self.election_dates[self.profile.title]["geo_version"]
        comparative_geos = geo_data.get_comparative_geos(self.geo)

        table = get_datatable(self.election_dates[self.profile.title]["turnout"])
        results = table.get_stat_data(
            self.geo,
            "total_votes",
            percent=True,
            total="registered_voters",
            year=self.election_dates[self.profile.title]["year"],
        )[0]["total_votes"]

        for comp_geo in comparative_geos:
            comp_results = table.get_stat_data(
                comp_geo,
                "total_votes",
                percent=True,
                total="registered_voters",
                year=self.election_dates[self.profile.title]["year"],
            )[0]["total_votes"]

            results["values"][comp_geo.geo_level] = comp_results["values"]["this"]
            results["numerators"][comp_geo.geo_level] = comp_results["numerators"][
                "this"
            ]

        self.geo.version = current_version
        return results

    def calculate_age_median(self):
        if self.profile.title == "Total Population":
            age_table = get_datatable("ageincompletedyears")
            objects = sorted(
                age_table.get_rows_for_geo(self.geo, self.session),
                key=lambda x: int(getattr(x, "age in completed years")),
            )
            median = calculate_median(objects, "age in completed years")
            return median

    def header(self):
        """
        Add calculation of the median age
        """
        head = super(VpuuIndicator, self).header()
        if self.profile.title == "Total Population":
            head["result"]["type"] = "number"
            head["result"]["values"]["this"] = self.calculate_age_median()
        elif self.profile.profile.name == "Elections":
            head["result"]["type"] = "number"
            head["result"]["values"] = self.election_turnout().get("values", {})
            head["result"]["numerators"] = self.election_turnout().get("numerators", {})
            extra = enhance_api_data(
                {
                    "type": "percent",
                    "values": self.extra_headers()["values"],
                    "numerators": self.extra_headers()["numerators"],
                    "name": "Of registered voters cast their vote",
                }
            )
            head["extra_results"].append(extra)
        # pdb.set_trace()
        head = enhance_api_data(head)

        return head

    def landcover(self):
        with dataset_context(year="2014"):
            try:
                distribution, total = get_stat_data(
                    [self.profile.field_name],
                    self.geo,
                    self.session,
                    table_universe=self.profile.universe,
                    table_dataset=self.profile.dataset,
                    exclude_zero=self.profile.exclude_zero,
                    percent=self.profile.percent,
                    recode=self.profile.recode,
                    key_order=self.profile.key_order,
                    exclude=self.profile.exclude,
                    order_by=self.profile.order_by,
                )
                group_remainder(distribution, self.profile.group_remainder)
                self.distribution = distribution
                return {"stat_values": distribution, "total": total}
            except DataNotFound:
                return {}

    def calculation(self):
        if self.profile.title == "National Land Cover":
            return self.landcover()
        elif self.profile.profile.name == "Elections":
            return self.elections()
        else:
            return super(VpuuIndicator, self).calculation()
