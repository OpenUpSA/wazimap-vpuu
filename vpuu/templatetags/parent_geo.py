from django import template

register = template.Library()


def get_parent_geo(geo_levels, geo):
    """
    only return the parent geo for a particular geography
    """
    compare_level = []
    for level in geo["parents"]:
        compare_level.append(level)
    return compare_level[:2]


register.filter("parent_geo", get_parent_geo)
