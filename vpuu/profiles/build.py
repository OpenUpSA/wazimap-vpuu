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
        else:
            return super(VpuuIndicator, self).calculation()
