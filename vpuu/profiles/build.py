from dynamic_profile.utils import BuildIndicator
from wazimap.data.tables import get_datatable
from wazimap.data.utils import (
    calculate_median,
    dataset_context,
    get_stat_data,
    group_remainder,
)
from wazimap.models.data import DataNotFound


class VpuuIndicator(BuildIndicator):
    """
    Add some custom changes for vpuu.
    """

    def __init__(self, *args, **kwargs):
        super(VpuuIndicator, self).__init__(*args, **kwargs)
        self.load_elections()

    def refuse_disposal(self):
        """
        show header for refuse
        """
        pass

    def water(self):
        """
        show header stats for water
        """
        pass

    def toilet(self):
        """
        Show header stats for toilet facilities
        """

        toilet_data, total_toilet = get_stat_data()

        total_flush_toilet = 0.0
        total_no_toilet = 0.0
        for key, data in self.distribution.items():
            if key.startswith("Flush") or key.startswith("Chemical"):
                total_flush_toilet += data["numerators"]["this"]
            if key == "None":
                total_no_toilet += data["numerators"]["this"]
        # "percentage_flush_toilet_access": {
        #     "name": "Have access to flush or chemical toilets",
        #     "numerators": {"this": total_flush_toilet},
        #     "values": {"this": percent(total_flush_toilet, total_toilet)},
        # },
        # "percentage_no_toilet_access": {
        #     "name": "Have no access to any toilets",
        #     "numerators": {"this": total_no_toilet},
        #     "values": {"this": percent(total_no_toilet, total_toilet)},
        return

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

        table = get_datatable(self.election_dates[self.profile.title]["turnout"])
        results = table.get_stat_data(
            self.geo,
            "registered_voters",
            percent=False,
            year=self.election_dates[self.profile.title]["year"],
        )[0]["registered_voters"]["values"]["this"]

        self.geo.version = current_version
        return results

    def extra_headers(self):
        current_version = self.geo.version
        self.geo.version = self.election_dates[self.profile.title]["geo_version"]

        table = get_datatable(self.election_dates[self.profile.title]["turnout"])
        results = table.get_stat_data(
            self.geo,
            "total_votes",
            percent=True,
            total="registered_voters",
            year=self.election_dates[self.profile.title]["year"],
        )[0]["total_votes"]["values"]["this"]
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
            head["value"] = self.calculate_age_median()
        elif self.profile.profile.name == "Elections":
            head["value"] = self.election_turnout()
            head["extra_headers"] = {
                "value": self.extra_headers(),
                "summary": "Of registered voters cast their vote",
            }
        else:
            head = head

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
