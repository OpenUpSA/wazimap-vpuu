from __future__ import division
from collections import OrderedDict
import logging

from wazimap.data.tables import get_datatable, get_table_id
from wazimap.data.utils import get_session, add_metadata
from wazimap.geo import geo_data
from dynamic_profile.models import IndicatorProfile, Profile
from dynamic_profile.utils import merge_dicts, Section, BuildProfile, BuildIndicator

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


PROFILE_SECTIONS = ("indicator",)


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

                # get profiles for comparative geometries
                for comp_geo in comparative_geos:
                    try:
                        merge_dicts(
                            data[section], func(comp_geo, session), comp_geo.geo_level
                        )
                    except KeyError as e:
                        msg = (
                            "Error merging data into %s for section '%s' from %s: KeyError: %s"
                            % (geo.geoid, section, comp_geo.geoid, e)
                        )
                        log.fatal(msg, exc_info=e)
                        raise ValueError(msg)
    finally:
        session.close()

    import json

    with open("example.json", "w") as f:
        json.dump(data, f)

    # exit()

    return data


def get_indicator_profile(geo, session):

    # profiles = Section(geo, session)
    # for profile in profiles.keys():
    #     indicators =

    section = Section(geo, session)
    return section.build(BuildProfile, VpuuIndicator)


def get_demographics_profile(geo, session):
    # population group
    pop_dist_data, total_pop = get_stat_data(
        ["population group"], geo, session, table_dataset="Census and Community Survey"
    )

    # language
    language_data, _ = get_stat_data(
        ["language"],
        geo,
        session,
        table_dataset="Census and Community Survey",
        order_by="-total",
    )
    language_most_spoken = language_data[language_data.keys()[0]]

    # age groups
    age_dist_data, total_age = get_stat_data(
        ["age groups in 5 years"],
        geo,
        session,
        table_dataset="Census and Community Survey",
        recode=COLLAPSED_AGE_CATEGORIES,
        key_order=(
            "0-9",
            "10-19",
            "20-29",
            "30-39",
            "40-49",
            "50-59",
            "60-69",
            "70-79",
            "80+",
        ),
    )

    # sex
    sex_data, _ = get_stat_data(
        ["gender"],
        geo,
        session,
        table_universe="Population",
        table_dataset="Census and Community Survey",
    )

    final_data = {
        "language_distribution": language_data,
        "language_most_spoken": language_most_spoken,
        "population_group_distribution": pop_dist_data,
        "age_group_distribution": age_dist_data,
        "sex_ratio": sex_data,
        "total_population": {"name": "People", "values": {"this": total_pop}},
    }

    if geo.square_kms:
        final_data["population_density"] = {
            "name": "people per square kilometre",
            "values": {"this": total_pop / geo.square_kms},
        }

    # median age/age category
    age_table = get_datatable("ageincompletedyears")
    objects = sorted(
        age_table.get_rows_for_geo(geo, session),
        key=lambda x: int(getattr(x, "age in completed years")),
    )

    # median age
    median = calculate_median(objects, "age in completed years")
    final_data["median_age"] = {"name": "Median age", "values": {"this": median}}

    # age category
    age_dist, _ = get_stat_data(
        ["age in completed years"],
        geo,
        session,
        table_dataset="Census and Community Survey",
        table_name="ageincompletedyearssimplified",
        key_order=["Under 18", "18 to 64", "65 and over"],
        recode={"< 18": "Under 18", ">= 65": "65 and over"},
    )
    final_data["age_category_distribution"] = age_dist

    # citizenship
    citizenship_dist, _ = get_stat_data(
        ["citizenship"],
        geo,
        session,
        table_dataset="Census and Community Survey",
        order_by="-total",
    )

    sa_citizen = citizenship_dist["Yes"]["numerators"]["this"]

    final_data["citizenship_distribution"] = citizenship_dist
    final_data["citizenship_south_african"] = {
        "name": "South African citizens",
        "values": {"this": percent(sa_citizen, total_pop)},
        "numerators": {"this": sa_citizen},
    }

    # migration
    province_of_birth_dist, _ = get_stat_data(
        ["province of birth"],
        geo,
        session,
        table_dataset="Census and Community Survey",
        exclude_zero=True,
        order_by="-total",
    )

    final_data["province_of_birth_distribution"] = province_of_birth_dist

    def region_recode(field, key):
        if key == "Born in South Africa":
            return "South Africa"
        else:
            return {"Not applicable": "Other"}.get(key, key)

    region_of_birth_dist, _ = get_stat_data(
        ["region of birth"],
        geo,
        session,
        table_dataset="Census and Community Survey",
        exclude_zero=True,
        order_by="-total",
        recode=region_recode,
    )

    if "South Africa" in region_of_birth_dist:
        born_in_sa = region_of_birth_dist["South Africa"]["numerators"]["this"]
    else:
        born_in_sa = 0

    final_data["region_of_birth_distribution"] = region_of_birth_dist
    final_data["born_in_south_africa"] = {
        "name": "Born in South Africa",
        "values": {"this": percent(born_in_sa, total_pop)},
        "numerators": {"this": born_in_sa},
    }

    return final_data


def get_households_profile(geo, session):
    # head of household
    # gender
    head_gender_dist, total_households = get_stat_data(
        ["gender of household head"],
        geo,
        session,
        table_universe="Households",
        order_by="gender of household head",
    )
    female_heads = head_gender_dist["Female"]["numerators"]["this"]

    # age
    u18_table = get_datatable("genderofheadofhouseholdunder18")
    objects = u18_table.get_rows_for_geo(geo, session)

    total_under_18 = float(sum(o[0] for o in objects))

    # tenure
    tenure_data, _ = get_stat_data(
        ["tenure status"],
        geo,
        session,
        table_universe="Households",
        recode=HOUSEHOLD_OWNERSHIP_RECODE,
        order_by="-total",
    )
    owned = 0
    for key, data in tenure_data.iteritems():
        if key.startswith("Owned"):
            owned += data["numerators"]["this"]

    # annual household income
    if geo.version == "2011":
        HOUSEHOLD_INCOME_RECODE = HOUSEHOLD_INCOME_RECODE_2011
    else:
        HOUSEHOLD_INCOME_RECODE = COLLAPSED_ANNUAL_INCOME_CATEGORIES
    income_dist_data, _ = get_stat_data(
        ["annual household income"],
        geo,
        session,
        table_universe="Households",
        exclude=["Unspecified", "Not applicable"],
        recode=HOUSEHOLD_INCOME_RECODE,
        key_order=HOUSEHOLD_INCOME_RECODE.values(),
    )

    # median income
    median = calculate_median_stat(income_dist_data)
    median_income = HOUSEHOLD_INCOME_ESTIMATE[median]

    # type of dwelling
    type_of_dwelling_dist, _ = get_stat_data(
        ["type of dwelling"],
        geo,
        session,
        table_universe="Households",
        recode=TYPE_OF_DWELLING_RECODE,
        order_by="-total",
    )
    informal = type_of_dwelling_dist["Shack"]["numerators"]["this"]

    # household goods
    household_goods, _ = get_stat_data(
        ["household goods"],
        geo,
        session,
        table_universe="Households",
        recode=HOUSEHOLD_GOODS_RECODE,
        key_order=sorted(HOUSEHOLD_GOODS_RECODE.values()),
    )

    return {
        "total_households": {
            "name": "Households",
            "values": {"this": total_households},
        },
        "owned": {
            "name": "Households fully owned or being paid off",
            "values": {"this": percent(owned, total_households)},
            "numerators": {"this": owned},
        },
        "type_of_dwelling_distribution": type_of_dwelling_dist,
        "informal": {
            "name": "Households that are informal dwellings (shacks)",
            "values": {"this": percent(informal, total_households)},
            "numerators": {"this": informal},
        },
        "tenure_distribution": tenure_data,
        "household_goods": household_goods,
        "annual_income_distribution": income_dist_data,
        "median_annual_income": {
            "name": "Average annual household income",
            "values": {"this": median_income},
        },
        "head_of_household": {
            "gender_distribution": head_gender_dist,
            "female": {
                "name": "Households with women as their head",
                "values": {"this": percent(female_heads, total_households)},
                "numerators": {"this": female_heads},
            },
            "under_18": {
                "name": "Households with heads under 18 years old",
                "values": {"this": total_under_18},
            },
        },
    }


def get_economics_profile(geo, session):
    profile = {}
    # income
    if geo.version == "2011":
        # distribution
        recode = COLLAPSED_MONTHLY_INCOME_CATEGORIES
        fields = ["employed individual monthly income"]
        income_dist_data, total_workers = get_stat_data(
            fields,
            geo,
            session,
            exclude=["Not applicable"],
            recode=recode,
            key_order=recode.values(),
        )

        # median income
        median = calculate_median_stat(income_dist_data)
        median_income = ESTIMATED_MONTHLY_INCOME_CATEGORIES[median]
        profile.update(
            {
                "individual_income_distribution": income_dist_data,
                "median_individual_income": {
                    "name": "Average monthly income",
                    "values": {"this": median_income},
                },
            }
        )
    else:
        # distribution
        recode = COLLAPSED_ANNUAL_INCOME_CATEGORIES
        fields = ["employed individual annual income"]
        income_dist_data, total_workers = get_stat_data(
            fields,
            geo,
            session,
            exclude=["Not applicable"],
            recode=recode,
            key_order=recode.values(),
        )

        # median income
        median = calculate_median_stat(income_dist_data)
        median_income = ESTIMATED_ANNUAL_INCOME_CATEGORIES[median]
        profile.update(
            {
                "individual_annual_income_distribution": income_dist_data,
                "median_annual_individual_income": {
                    "name": "Average annual income",
                    "values": {"this": median_income},
                },
            }
        )

    # employment status
    employ_status, total_workers = get_stat_data(
        ["official employment status"],
        geo,
        session,
        exclude=["Age less than 15 years", "Not applicable"],
        order_by="official employment status",
        table_name="officialemploymentstatus",
    )

    # sector
    sector_dist_data, _ = get_stat_data(
        ["type of sector"],
        geo,
        session,
        exclude=["Not applicable"],
        order_by="type of sector",
    )

    profile.update(
        {
            "employment_status": employ_status,
            "sector_type_distribution": sector_dist_data,
        }
    )

    # access to internet
    if current_context().get("year") == "latest":
        internet_access_dist, total_households = get_stat_data(
            ["access to internet"],
            geo,
            session,
            recode=INTERNET_ACCESS_RECODE,
            table_name="accesstointernet_2016",
        )

        profile.update({"internet_access_distribution": internet_access_dist})

    else:
        internet_access_dist, total_with_access = get_stat_data(
            ["access to internet"],
            geo,
            session,
            exclude=["No access to internet"],
            order_by="access to internet",
        )
        _, total_without_access = get_stat_data(
            ["access to internet"], geo, session, only=["No access to internet"]
        )
        total_households = total_with_access + total_without_access

        profile.update(
            {
                "internet_access_distribution": internet_access_dist,
                "internet_access": {
                    "name": "Households with internet access",
                    "values": {"this": percent(total_with_access, total_households)},
                    "numerators": {"this": total_with_access},
                },
            }
        )

    return profile


def get_service_delivery_profile(geo, session):
    # water source
    water_src_data, total_wsrc = get_stat_data(
        ["source of water"],
        geo,
        session,
        recode=SHORT_WATER_SOURCE_CATEGORIES,
        order_by="-total",
    )

    # water from a service provider
    total_water_sp = 0.0
    perc_water_sp = 0.0

    if current_context().get("year") == "latest":
        water_supplier_data, total_wspl = get_stat_data(
            ["supplier of water"],
            geo,
            session,
            recode=SHORT_WATER_SUPPLIER_CATEGORIES,
            order_by="-total",
        )

        water_sp = ["Service provider", "Water scheme"]

        for key in water_sp:
            if key in water_supplier_data:
                total_water_sp += water_supplier_data[key]["numerators"]["this"]

        perc_water_sp = percent(total_water_sp, total_wspl)

    else:
        if "Service provider" in water_src_data:
            total_water_sp = water_src_data["Service provider"]["numerators"]["this"]
            perc_water_sp = percent(total_water_sp, total_wsrc)

    percentage_water_from_service_provider = {
        "name": "Are getting water from a regional or local service provider",
        "numerators": {"this": total_water_sp},
        "values": {"this": perc_water_sp},
    }

    # refuse disposal
    refuse_disp_data, total_ref = get_stat_data(
        ["refuse disposal"],
        geo,
        session,
        recode=SHORT_REFUSE_DISPOSAL_CATEGORIES,
        order_by="-total",
    )

    total_ref_sp = 0.0
    for k, v in refuse_disp_data.iteritems():
        if k.startswith("Service provider"):
            total_ref_sp += v["numerators"]["this"]

    sp_name_2011 = (
        "Are getting refuse disposal from a local authority or private company"
    )
    sp_name_2016 = "Are getting refuse disposal from a local authority, private company or community members"

    percentage_ref_disp_from_service_provider = {
        "name": sp_name_2011
        if str(current_context().get("year")) == "2011"
        else sp_name_2016,
        "numerators": {"this": total_ref_sp},
        "values": {"this": percent(total_ref_sp, total_ref)},
    }

    # electricity
    if geo.version == "2011" and str(current_context().get("year")) == "2011":
        elec_attrs = [
            "electricity for cooking",
            "electricity for heating",
            "electricity for lighting",
        ]

        elec_table = get_datatable("electricityforcooking_electricityforheating_electr")
        objects = elec_table.get_rows_for_geo(geo, session)

        total_elec = 0.0
        total_some_elec = 0.0
        elec_access_data = {
            "total_all_elec": {
                "name": "Have electricity for everything",
                "numerators": {"this": 0.0},
            },
            "total_some_not_all_elec": {
                "name": "Have electricity for some things",
                "numerators": {"this": 0.0},
            },
            "total_no_elec": {"name": "No electricity", "numerators": {"this": 0.0}},
        }
        for obj in objects:
            total_elec += obj.total
            has_some = False
            has_all = True
            for attr in elec_attrs:
                val = not getattr(obj, attr).startswith("no ")
                has_all = has_all and val
                has_some = has_some or val
            if has_some:
                total_some_elec += obj.total
            if has_all:
                elec_access_data["total_all_elec"]["numerators"]["this"] += obj.total
            elif has_some:
                elec_access_data["total_some_not_all_elec"]["numerators"][
                    "this"
                ] += obj.total
            else:
                elec_access_data["total_no_elec"]["numerators"]["this"] += obj.total
        set_percent_values(elec_access_data, total_elec)
        add_metadata(
            elec_access_data,
            elec_table,
            elec_table.get_release(current_context().get("year")),
        )

    if current_context().get("year") == "latest":
        # We don't have this data for 2011
        elec_access, _ = get_stat_data(
            ["access to electricity"],
            geo,
            session,
            table_universe="Population",
            recode=ELECTRICITY_ACCESS_RECODE,
            order_by="-total",
        )

    # toilets
    toilet_data, total_toilet = get_stat_data(
        ["toilet facilities"],
        geo,
        session,
        exclude_zero=True,
        recode=COLLAPSED_TOILET_CATEGORIES,
        order_by="-total",
    )

    total_flush_toilet = 0.0
    total_no_toilet = 0.0
    for key, data in toilet_data.iteritems():
        if key.startswith("Flush") or key.startswith("Chemical"):
            total_flush_toilet += data["numerators"]["this"]
        if key == "None":
            total_no_toilet += data["numerators"]["this"]

    profile = {
        "water_source_distribution": water_src_data,
        "percentage_water_from_service_provider": percentage_water_from_service_provider,
        "refuse_disposal_distribution": refuse_disp_data,
        "percentage_ref_disp_from_service_provider": percentage_ref_disp_from_service_provider,
        "percentage_flush_toilet_access": {
            "name": "Have access to flush or chemical toilets",
            "numerators": {"this": total_flush_toilet},
            "values": {"this": percent(total_flush_toilet, total_toilet)},
        },
        "percentage_no_toilet_access": {
            "name": "Have no access to any toilets",
            "numerators": {"this": total_no_toilet},
            "values": {"this": percent(total_no_toilet, total_toilet)},
        },
        "toilet_facilities_distribution": toilet_data,
    }

    if current_context().get("year") == "latest":
        profile.update(
            {
                "water_supplier_distribution": water_supplier_data,
                "electricity_access": elec_access,
                "percentage_no_electricity_access": {
                    "name": "Have no access to electricity",
                    "numerators": elec_access["No access to electricity"]["numerators"],
                    "values": elec_access["No access to electricity"]["values"],
                },
            }
        )

    if geo.version == "2011":
        profile.update(
            {
                "percentage_electricity_access": {
                    "name": "Have electricity for at least one of cooking, heating or lighting",
                    "numerators": {"this": total_some_elec},
                    "values": {"this": percent(total_some_elec, total_elec)},
                },
                "electricity_access_distribution": elec_access_data,
            }
        )
    return profile


def set_percent_values(data, total):
    for fields in data.values():
        fields["values"] = {"this": percent(fields["numerators"]["this"], total)}


def get_education_profile(geo, session):
    edu_dist_data, total_over_20 = get_stat_data(
        ["highest educational level"],
        geo,
        session,
        recode=COLLAPSED_EDUCATION_CATEGORIES,
        table_universe="Individuals 20 and older",
        key_order=EDUCATION_KEY_ORDER,
    )

    GENERAL_EDU = (
        EDUCATION_GET_OR_HIGHER
        if str(current_context().get("year")) == "2011"
        else EDUCATION_GET_OR_HIGHER_2016
    )
    general_edu, total_general_edu = get_stat_data(
        ["highest educational level"],
        geo,
        session,
        table_universe="Individuals 20 and older",
        only=GENERAL_EDU,
    )

    FURTHER_EDU = (
        EDUCATION_FET_OR_HIGHER
        if str(current_context().get("year")) == "2011"
        else EDUCATION_FET_OR_HIGHER_2016
    )
    further_edu, total_further_edu = get_stat_data(
        ["highest educational level"],
        geo,
        session,
        table_universe="Individuals 20 and older",
        only=FURTHER_EDU,
    )

    edu_split_data = {
        "percent_general_edu": {
            "name": "Completed Grade 9 or higher",
            "numerators": {"this": total_general_edu},
            "values": {"this": round(total_general_edu / total_over_20 * 100, 2)},
        },
        "percent_further_edu": {
            "name": "Completed Matric or higher",
            "numerators": {"this": total_further_edu},
            "values": {"this": round(total_further_edu / total_over_20 * 100, 2)},
        },
        "metadata": general_edu["metadata"],
    }

    profile = {
        "educational_attainment_distribution": edu_dist_data,
        "educational_attainment": edu_split_data,
    }

    return profile


def get_children_profile(geo, session):
    profile = {}
    # age
    child_adult_dist, _ = get_stat_data(
        ["age in completed years"],
        geo,
        session,
        table_name="ageincompletedyearssimplified",
        recode={
            "< 18": "Children (< 18)",
            "18 to 64": "Adults (>= 18)",
            ">= 65": "Adults (>= 18)",
        },
        key_order=["Children (< 18)", "Adults (>= 18)"],
    )

    # parental survival
    survival, total = get_stat_data(["mother alive", "father alive"], geo, session)

    parental_survival_dist = OrderedDict()
    parental_survival_dist["metadata"] = survival["metadata"]

    parental_survival_dist["Both parents"] = survival["Yes"]["Yes"]
    parental_survival_dist["Both parents"]["name"] = "Both parents"

    parental_survival_dist["Neither parent"] = survival["No"]["No"]
    parental_survival_dist["Neither parent"]["name"] = "Neither parent"

    parental_survival_dist["One parent"] = survival["Yes"]["No"]
    parental_survival_dist["One parent"]["numerators"]["this"] += survival["No"]["Yes"][
        "numerators"
    ]["this"]

    rest = (
        total
        - parental_survival_dist["Both parents"]["numerators"]["this"]
        - parental_survival_dist["Neither parent"]["numerators"]["this"]
        - parental_survival_dist["One parent"]["numerators"]["this"]
    )

    parental_survival_dist["Uncertain"] = {
        "name": "Uncertain",
        "numerators": {"this": rest},
        "values": {"this": percent(rest, total)},
    }

    # gender
    gender_dist, _ = get_stat_data(
        ["gender"], geo, session, table_universe="Children under 18"
    )

    # school

    # NOTE: this data is incompatible with some views (check out
    # https://github.com/censusreporter/censusreporter/issues/78)
    #
    # school_attendance_dist, total_school_aged = get_stat_data(
    #     ['present school attendance', 'age in completed years'],
    #     geo, session,
    # )
    # school_attendance_dist['Yes']['metadata'] = \
    #         school_attendance_dist['metadata']
    # school_attendance_dist = school_attendance_dist['Yes']
    # total_attendance = sum(d['numerators']['this'] for d in
    #                        school_attendance_dist.values()
    #                        if 'numerators' in d)

    # school attendance
    school_attendance_dist, total_school_aged = get_stat_data(
        ["present school attendance"],
        geo,
        session,
        recode=COLLAPSED_ATTENDANCE_CATEGORIES,
    )
    total_attendance = school_attendance_dist["Yes"]["numerators"]["this"]

    # education level
    education17_dist, _ = get_stat_data(
        ["highest educational level"],
        geo,
        session,
        table_universe="17-year-old children",
        recode=COLLAPSED_EDUCATION_CATEGORIES,
        key_order=EDUCATION_KEY_ORDER,
    )

    # employment
    employment_dist, total_15to17 = get_stat_data(
        ["official employment status"],
        geo,
        session,
        table_universe="Children 15 to 17",
        exclude=["Not applicable"],
    )
    total_in_labour_force = float(
        sum(
            v["numerators"]["this"]
            for k, v in employment_dist.iteritems()
            if COLLAPSED_EMPLOYMENT_CATEGORIES.get(k, None) == "In labour force"
        )
    )

    employment_indicators = {
        "percent_in_labour_force": {
            "name": "Of children between 15 and 17 are in the labour force",
            "numerators": {"this": total_in_labour_force},
            "values": {"this": percent(total_in_labour_force, total_15to17)},
        },
        "employment_distribution": employment_dist,
    }
    # median income
    # monthly or annual
    if geo.version == "2011":
        income_dist_data, total_workers = get_stat_data(
            ["individual monthly income"],
            geo,
            session,
            table_universe="Children 15 to 17 who are employed",
            exclude=["Not applicable"],
            recode=COLLAPSED_MONTHLY_INCOME_CATEGORIES,
            key_order=COLLAPSED_MONTHLY_INCOME_CATEGORIES.values(),
        )
        median = calculate_median_stat(income_dist_data)
        median_income = ESTIMATED_MONTHLY_INCOME_CATEGORIES[median]
        employment_indicators.update(
            {
                "median_income": {
                    "name": "Average monthly income of employed children between 15 and 17",
                    "values": {"this": median_income},
                }
            }
        )
    else:
        income_dist_data, total_workers = get_stat_data(
            ["individual annual income"],
            geo,
            session,
            table_universe="Children 15 to 17 who are employed",
            exclude=["Not applicable"],
            recode=COLLAPSED_ANNUAL_INCOME_CATEGORIES,
            key_order=COLLAPSED_ANNUAL_INCOME_CATEGORIES.values(),
        )
        median = calculate_median_stat(income_dist_data)
        median_income = ESTIMATED_ANNUAL_INCOME_CATEGORIES[median]
        employment_indicators.update(
            {
                "median_annual_income": {
                    "name": "Average annual income of employed children between 15 and 17",
                    "values": {"this": median_income},
                }
            }
        )

    profile.update(
        {
            "demographics": {
                "child_adult_distribution": child_adult_dist,
                "total_children": {
                    "name": "Children",
                    "values": {
                        "this": child_adult_dist["Children (< 18)"]["numerators"][
                            "this"
                        ]
                    },
                },
                "gender_distribution": gender_dist,
                "parental_survival_distribution": parental_survival_dist,
                "percent_no_parent": {
                    "name": "Of children 14 and under have no living biological parents",
                    "values": parental_survival_dist["Neither parent"]["values"],
                    "numerators": parental_survival_dist["Neither parent"][
                        "numerators"
                    ],
                },
            },
            "school": {
                "school_attendance_distribution": school_attendance_dist,
                "percent_school_attendance": {
                    "name": "School-aged children (5 to 17 years old) are in school",
                    "numerators": {"this": total_school_aged},
                    "values": {
                        "this": percent(
                            float(total_attendance), float(total_school_aged)
                        )
                    },
                },
                "education17_distribution": education17_dist,
            },
            "employment": employment_indicators,
        }
    )
    return profile


def get_child_households_profile(geo, session):
    # head of household
    # gender
    head_gender_dist, total_households = get_stat_data(
        ["gender of head of household"],
        geo,
        session,
        table_universe="Households headed by children under 18",
        order_by="gender of head of household",
    )
    female_heads = head_gender_dist["Female"]["numerators"]["this"]

    # annual household income
    if geo.version == "2011":
        HOUSEHOLD_INCOME_RECODE = HOUSEHOLD_INCOME_RECODE_2011
    else:
        HOUSEHOLD_INCOME_RECODE = COLLAPSED_ANNUAL_INCOME_CATEGORIES
    income_dist_data, _ = get_stat_data(
        ["annual household income"],
        geo,
        session,
        exclude=["Unspecified"],
        recode=HOUSEHOLD_INCOME_RECODE,
        key_order=HOUSEHOLD_INCOME_RECODE.values(),
        table_name="annualhouseholdincomeunder18",
    )

    # median income
    median = calculate_median_stat(income_dist_data)
    median_income = HOUSEHOLD_INCOME_ESTIMATE[median]

    # type of dwelling
    type_of_dwelling_dist, _ = get_stat_data(
        ["type of main dwelling"],
        geo,
        session,
        recode=TYPE_OF_DWELLING_RECODE,
        order_by="-total",
    )
    informal = type_of_dwelling_dist["Shack"]["numerators"]["this"]

    return {
        "total_households": {
            "name": "Households with heads under 18 years old",
            "values": {"this": total_households},
        },
        "type_of_dwelling_distribution": type_of_dwelling_dist,
        "informal": {
            "name": "Child-headed households that are informal dwellings (shacks)",
            "values": {"this": percent(informal, total_households)},
            "numerators": {"this": informal},
        },
        "annual_income_distribution": income_dist_data,
        "median_annual_income": {
            "name": "Average annual child-headed household income",
            "values": {"this": median_income},
        },
        "head_of_household": {
            "gender_distribution": head_gender_dist,
            "female": {
                "name": "Child-headed households with women as their head",
                "values": {"this": percent(female_heads, total_households)},
                "numerators": {"this": female_heads},
            },
        },
    }


def get_crime_profile(geo, session):
    with dataset_context(year="2014"):
        child_crime, total = get_stat_data(
            ["crime"],
            geo,
            session,
            table_universe="Crimes",
            only=["Neglect and ill-treatment of children"],
            percent=False,
        )

    return {
        "metadata": child_crime["metadata"],
        "crime_against_children": {
            "name": "Crimes of neglect and ill-treatment of children in 2014",
            "values": {"this": total},
            "metadata": child_crime["metadata"],
        },
    }
