import logging
from datetime import date, datetime, timedelta
from typing import List, Optional, Union, Tuple
from dateutil import parser as date_parser

import dash_core_components as dcc
import pandas as pd
import plotly.graph_objects as go
from flask_security import current_user
from sqlalchemy import and_, asc, desc

from database import db
from structure.measurements import OTMeasurement
from structure.organization import Team
from visuals.base import VisualController
from visuals.shared import fix_timedelta_plot

DateLike = Union[date, datetime, str]


class OvertimeChartController(VisualController):
    """
    Visual for showing worktime-data in a bar-chart. Can be filtered by
    period and by teams.
    """

    def __init__(self, chart_html_id: str = "overtime-chart"):
        self.chart_html_id = chart_html_id
        self.date_format = "%B %Y"
        self.axis_label_period_format = "%B"
        self.tick_format = "%H:%M"

    def get_latest_date(self) -> datetime:
        """ Return latest date for which data is available """
        result = (
            db.session.query(OTMeasurement.measurement_date)
            .filter(OTMeasurement.team_id.in_(current_user.readable_team_ids))
            .order_by(desc(OTMeasurement.measurement_date))
            .limit(1)
            .first()
        )
        if result is None:
            return datetime.now()
        else:
            return result[0]

    def get_earliest_date(self) -> datetime:
        """ Return earliest date for which data is available """
        result = (
            db.session.query(OTMeasurement.measurement_date)
            .filter(OTMeasurement.team_id.in_(current_user.readable_team_ids))
            .order_by(asc(OTMeasurement.measurement_date))
            .limit(1)
            .first()
        )
        if result is None:
            return datetime.now()
        else:
            return result[0]

    def draw(self):
        """
        Draw bar-chart showing overtime data.
        """
        data, layout = self.update(self.get_latest_date(), self.get_latest_date())
        return dcc.Graph(
            id=self.chart_html_id, figure=go.Figure(data=data, layout=layout)
        )

    def __safe_parse_to_ot_period(self, input_date: DateLike) -> date:
        """ Parse `input_date` to an overtime period of type `date` in a safe
            way """

        # Parse date with dateutil in case we were given a string.
        if isinstance(input_date, str):
            input_date = date_parser.parse(input_date)

        # (down)cast input_date to `date`-type and set day=1
        try:
            selected_period = date(year=input_date.year, month=input_date.month, day=1)
        except AttributeError:
            logging.warning(
                f"Error parsing selected date. "
                f"Date was {input_date}"
                f" type={type(input_date)}."
                " Will default to current month."
            )
            selected_period = date(
                year=date.today().year, month=date.today().month, day=1
            )

        return selected_period

    def __load_data(
        self,
        selected_start_date: date,
        selected_end_date: date,
        selected_teams: Optional[List[int]] = None,
    ) -> pd.DataFrame:
        # Set up SQL-filter for teams. If selection is None, all teams are selected.
        if selected_teams is None:
            filter_teams = True
        else:
            filter_teams = Team.team_id.in_(selected_teams)

        # Load overtime-data from database
        query = (
            db.session.query(
                OTMeasurement.measurement_date,
                OTMeasurement.overtime,
                OTMeasurement.workdays_fix,
                OTMeasurement.workdays_actual,
                Team.team_id.label("team_id"),
                Team.name.label("team_name"),
            )
            .join(Team)
            .filter(
                and_(
                    filter_teams,
                    OTMeasurement.measurement_date.between(
                        selected_start_date, selected_end_date
                    ),
                    Team.team_id.in_(current_user.readable_team_ids),
                )
            )
        )

        result = pd.read_sql(
            query.statement, db.session.bind, parse_dates=["measurement_date"],
        )

        """
        If data was successfully retrieved and is not empty, do the following:
            1. For each row, calculate overtime per day
            2. Group the entries, so that the data can be sliced by period and team
                - Aggregate overtime per day by min, mean and max
                - Calculate number of team members for the given period
            3. Sort the data by teams and dates
        If there was no data, return an empty dataframe and return.
        """
        if result.empty:
            logging.info("No overtime data for the active filter.")
            return pd.DataFrame()

        # 1. Calculate overtime per day.
        # TODO: Make this safe for DivisionByZero-error.
        result["ot_per_day"] = result["overtime"] / result["workdays_actual"]
        # TODO: Need to fix
        result["num_members"] = 1

        # 2. Group & aggregate
        data = result.groupby(["measurement_date", "team_name"]).agg(
            {"ot_per_day": list}
        )
        data.reset_index(inplace=True)

        # 3. Sort by teams and dates & label each record
        data.sort_values(by=["team_name", "measurement_date"], inplace=True)
        data["label"] = data.apply(
            lambda x: self._data_label(x["team_name"], x["measurement_date"]), axis=1,
        )

        return data

    def _data_label(self, team_name: str, measurement_date: DateLike) -> str:
        return "{team_name} {measurement_date}".format(
            team_name=team_name,
            measurement_date=self.__safe_parse_to_ot_period(measurement_date).strftime(
                self.axis_label_period_format
            ),
        )

    def update(
        self,
        selected_start_date: DateLike,
        selected_end_date: DateLike,
        selected_teams: Optional[List[int]] = None,
    ) -> Tuple[List, go.Layout]:
        """
        Return traces (bars) and layout of overtime chart for the month in
            `selected_date`, showing the teams in `selected_teams`.

        selected_date   - Display overtime chart for this month.
                            Accepts `date`, `datetime` or a `str` (in which
                            case update() tries to parse it into a date)
        selected_teams  - A list of IDs for the teams which should be displayed
                            in the chart.
        """
        selected_start_period = self.__safe_parse_to_ot_period(selected_start_date)
        selected_end_period = self.__safe_parse_to_ot_period(selected_end_date)

        # Retrieve data from database
        data = self.__load_data(
            selected_start_date=selected_start_period,
            selected_end_date=selected_end_period,
            selected_teams=selected_teams,
        )

        traces = [
            go.Box(
                x=[
                    fix_timedelta_plot(
                        ot_per_day if ot_per_day > timedelta(0) else timedelta(0)
                    )
                    for ot_per_day in row["ot_per_day"]
                ],
                name=row["label"],
                marker_color="#f56565",
            )
            for _, row in data.iterrows()
        ]

        # Create readable title for the chart
        selected_start_period_readable = selected_start_period.strftime(
            self.date_format
        )
        selected_end_period_readable = selected_end_period.strftime(self.date_format)
        if selected_start_period_readable != selected_end_period_readable:
            title = (
                f"Overtime for {selected_start_period_readable} to"
                f" {selected_end_period_readable}"
            )
        else:
            title = f"Overtime for {selected_start_period_readable}"

        layout = go.Layout(
            autosize=True,
            margin=dict(t=70, l=30, r=30, b=30),
            legend_orientation="h",
            font=dict(size=12),
            bargap=0.2,
            title=go.layout.Title(text=title),
            # Configure as a stacked bar chart
            barmode="stack",
            # X axis ticks
            xaxis=dict(dtick=30 * 60 * 1000, tickformat=self.tick_format),
            # We reverse the yaxis, because it starts at the bottom by default.
            yaxis=dict(dtick=1, type="category", autorange="reversed", automargin=True),
            showlegend=False,
        )

        return traces, layout
