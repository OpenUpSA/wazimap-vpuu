from __future__ import division
from collections import OrderedDict
import logging

from wazimap.data.tables import get_datatable, get_table_id
from wazimap.data.utils import get_session, add_metadata
from wazimap.geo import geo_data
from dynamic_profile.models import IndicatorProfile, Profile
from dynamic_profile.utils import merge_dicts, Section, BuildProfile, BuildIndicator
from wazimap.models.data import DataNotFound

from wazimap.data.utils import (
    collapse_categories,
    calculate_median,
    calculate_median_stat,
    group_remainder,
    get_stat_data,
    percent,
    current_context,
    dataset_context,
)
from .build import VpuuIndicator


log = logging.getLogger(__name__)


PROFILE_SECTIONS = ("indicator", "population")


def get_profile(geo, profile_name, request):
    session = get_session()

    try:
        comparative_geos = geo_data.get_comparative_geos(geo)
        data = {}
        data["primary_release_year"] = current_context().get("year")

        sections = list(PROFILE_SECTIONS)

        for section in sections:
            function_name = "get_%s_profile" % section
            if function_name in globals():
                func = globals()[function_name]
                data[section] = func(geo, session)
                # if section == "indicator":
                #     # get profiles for comparative geometries
                #     for comp_geo in comparative_geos:
                #         try:
                #             merge_dicts(
                #                 data[section],
                #                 func(comp_geo, session),
                #                 comp_geo.geo_level,
                #             )
                #         except KeyError as e:
                #             msg = (
                #                 "Error merging data into %s for section '%s' from %s: KeyError: %s"
                #                 % (geo.geoid, section, comp_geo.geoid, e)
                #             )
                #             log.fatal(msg, exc_info=e)
                #             raise ValueError(msg)
    finally:
        session.close()

    return data


def get_indicator_profile(geo, session):

    section = Section(geo, session)
    return section.build(BuildProfile, VpuuIndicator)


def get_population_profile(geo, session):
    """
    Get population of geography
    """
    try:
        _, total_pop = get_stat_data(
            ["population group"],
            geo,
            session,
            table_dataset="Census and Community Survey",
        )
        return {
            "geography_population": total_pop,
            "density": total_pop / geo.square_kms,
        }
    except DataNotFound:
        return {"geography_population": "N/A", "density": "N/A"}
