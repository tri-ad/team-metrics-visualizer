import logging
from datetime import datetime, timedelta, time, date
import re
import pandas as pd


def to_timedelta(value) -> timedelta:
    """
    Tries to cast a value to a Python timedelta-object. It supports datetime, time and
    nicely formatted strings.
    It will return timedelta(0) in case it fails.

    :param value: The value to cast to timedelta.
    :return: A timedelta-object.
    """

    # For values >=24hrs, Pandas converts them to a datetime object.
    # For values <24hrs, Pandas converts them to time object.
    if isinstance(value, timedelta):
        return value
    elif isinstance(value, datetime):
        return value - datetime(1900, 1, 1) + timedelta(hours=24)
    elif isinstance(value, time):
        return datetime.combine(date.min, value) - datetime.min
    elif isinstance(value, str):
        duration_regex = re.compile(
            r"^(?P<sign>-?)(?P<hours>[0-9]+?):(?P<minutes>[0-9]{2})$"
        )
        parts = duration_regex.match(value.strip())
        if parts is not None:
            sign = parts.group("sign")
            hours = float(parts.group("hours"))
            minutes = float(parts.group("minutes"))
            if sign == "-":
                hours = hours * (-1)
                minutes = minutes * (-1)
            return timedelta(hours=hours, minutes=minutes)
        else:
            logging.warning(
                "Could not convert overtime value to timedelta "
                "object. "
                f"Values was {value} and type was {type(value)}."
            )

    else:
        logging.warning(
            "Could not convert overtime value to timedelta object. "
            f"Value was {value} and type was {type(value)}."
        )

    return timedelta(0)


def td_remove_microseconds(td: timedelta) -> timedelta:
    """
    Sets microseconds of a timedelta-object to 0.

    :param td: Timedelta object
    :return: Timedelta object with microseconds set to 0.
    """

    try:
        return td - timedelta(microseconds=td.microseconds)
    except ValueError:
        logging.warning(
            "There was an error removing the microseconds from a"
            f" timedelta object. The object was {td}."
        )
        return timedelta(0)
