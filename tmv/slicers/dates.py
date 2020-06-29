from typing import List
from datetime import datetime

import dash_core_components as dcc
from slicers.state import callback_slicer_state_saving, load_slicer_value


def convert_date_to_str(d):
    return d.strftime("%Y-%m-%d")


def date_picker(
    selected=datetime.today(),
    max_date=datetime.today(),
    min_date=None,
    display_format="YY/MM/DD",
    display_format_month="MMM, YY",
    html_element_id="date_picker",
) -> List:
    """
    Creates a control for selecting a single date.
    """

    picker = dcc.DatePickerSingle(
        id=html_element_id,
        max_date_allowed=max_date,
        min_date_allowed=min_date,
        initial_visible_month=selected,
        date=selected,
        first_day_of_week=1,
        display_format=display_format,
        month_format=display_format_month,
    )

    return [picker]


def date_range_picker(
    max_date=datetime.today(),
    min_date=None,
    start_date=datetime.today(),
    end_date=datetime.today(),
    display_format="YY/MM/DD",
    display_format_month="MMM, YY",
    html_element_id="date_range_picker",
) -> List:
    """
    Creates a control for selecting a range of dates.
    """

    max_date = convert_date_to_str(max_date) if max_date else None
    min_date = convert_date_to_str(min_date) if min_date else None
    start_date = convert_date_to_str(start_date) if start_date else None
    end_date = convert_date_to_str(end_date) if end_date else None

    saved_values = load_slicer_value(
        "date_range_picker",
        value_type=list,
        default=[start_date, end_date, min_date, max_date],
    )

    *_, saved_min_date, saved_max_date = saved_values

    if saved_min_date == min_date and saved_max_date == max_date:
        saved_start_date, saved_end_date, *_ = saved_values
        start_date = saved_start_date
        end_date = saved_end_date

    picker = dcc.DatePickerRange(
        id=html_element_id,
        min_date_allowed=min_date,
        max_date_allowed=max_date,
        initial_visible_month=start_date,
        start_date=start_date,
        end_date=end_date,
        first_day_of_week=1,
        display_format=display_format,
        month_format=display_format_month,
    )

    return [picker]


def callback_date_range_picker_state_saving(app, picker_id):
    callback_slicer_state_saving(
        app,
        "date_range_picker",
        picker_id,
        ["start_date", "end_date", "min_date_allowed", "max_date_allowed"],
    )
