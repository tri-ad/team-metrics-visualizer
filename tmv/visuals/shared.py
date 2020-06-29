import pandas as pd


def fix_timedelta_plot(timedelta_df):
    """
    Fix the display of timedelta-values in a plotly-plot.

    Background: Plotly/dash does currently (2019/8/21) not support plotting of
    timedelta-values. When plotting values of type timedelta, plotly makes
    weird labels on the axis. A workaround is to turn them into datetime-values
    by adding the date 1970/1/1.

    Ref.: https://community.plot.ly/t/timeseries-plot-with-timedelta-axis/23560
    and: https://github.com/plotly/plotly.py/issues/801#issuecomment-317174985
    """
    return timedelta_df + pd.to_datetime("1970/1/1")
