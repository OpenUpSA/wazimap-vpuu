from django import template

register = template.Library()


def charts(children, chart_design):
    """
    Sort the charts so that they can be prepared for the print design
    """
    count = 0
    for child in children:
        child["index_count"] = count
        count += 1

    widths = []
    for child in children:
        if child["chart_design"] == chart_design:
            widths.append(child)

    if chart_design == "--half-width":
        widths = [widths[i : i + 2] for i in range(0, len(widths), 2)]
    return widths


register.filter("charts", charts)
