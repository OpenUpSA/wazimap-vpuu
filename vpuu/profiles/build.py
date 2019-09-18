from dynamic_profile.utils import BuildIndicator
from wazimap.data.tables import get_datatable
from wazimap.data.utils import calculate_median


class VpuuIndicator(BuildIndicator):
    """
    Add some custom changes for vpuu.
    """

    def __init__(self, *args, **kwargs):
        super(VpuuIndicator, self).__init__(*args, **kwargs)

    def calculate_age_median(self):
        if self.profile.title == "Age":
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
        if self.profile.title == "Age":
            head["value"] = self.calculate_age_median()
        return head
