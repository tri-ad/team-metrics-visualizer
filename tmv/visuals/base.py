import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import List

import plotly.graph_objects as go
from dateutil import rrule
from dateutil.tz import tzutc
from flask_security import current_user

from structure.events import Sprint
from structure.project import Activity


class VisualController(ABC):
    """
    Base class for all visuals

    Visuals are self-contained and can be integrated in one or multiple
    dashboards. They change based on changed values of controls in the
    dashboard.
    Visuals can be charts (line, bar, column etc.), data tables or also text
    views.
    A visual maintains its own database-session and can query for additional
    data if necessary (after a change of filters, for example).
    Visuals provide at least two methods:

    - `draw()`: Initially draws the visual on the dashboard. You should
      choose initial filters/ranges for your data that make sense.
    - `update()`: Update the visual after some controls have been used to
      change range of data, filters etc. You should return values for the
      properties of the dash component you want to change (like data,
      layout, etc.) and call this method in the callback-function which
      is connected to the respective control of the dashboard.
    """

    @abstractmethod
    def draw(self, *args, **kwargs):
        """
        Implement this method to initially draw your visual.
        """
        pass

    @abstractmethod
    def update(self, *args, **kwargs):
        """
        Implement this method to update your visual.
        Usually update is called in a callback-method. It usually takes values
        from the controls in a dashboard and returns new data (and layout, if
        necessary) for the visual.
        """
        pass


class SprintVisualController(VisualController):
    """
    Base class for visuals depicting a Sprint with x-axis
    as dates of the Sprint and y-axis as Story Points.
    The layout, selection and syncing of data are
    already implemented for convenience.
    """

    @abstractmethod
    def _get_plots(self, *args, **kwargs):
        """
        Implement this method to get the data for the sprint
        """
        pass

    def _get_layout(self, index: list) -> go.Layout:
        """
        Builds and returns the layout for the chart.
        Notes:
        - xaxis.rangebreaks allows us to skip weekends
        - The xaxis.tick* are setup that way because xaxis.rangebreaks
          causes some issues otherwise (e.g., wrong data on tick).
          Leaving it blank (auto) does not provide good results. Only
          two ticks show up.
        :param index: List of dates for the x axis.
        """
        index_str = [dt.strftime("%b %d (%a)") for dt in index]
        return go.Layout(
            title=dict(text="Sprint Chart", x=0.07, xanchor="left",),
            xaxis=dict(
                title_text="Date (weekends excluded)",
                tickmode="array",
                tickvals=index[::2],
                ticktext=index_str[::2],
                tickformat="%b %d (%a)",
                rangebreaks=[dict(bounds=["sat", "mon"])],
                range=[index[0], index[-1]],
            ),
            yaxis=dict(title_text="Story Points",),
            legend=dict(orientation="h", x=1, xanchor="right", y=1.2,),
        )

    def check_for_data(self, sprint):
        if sprint.should_be_updated:
            logging.debug(f"sprint {sprint.sprint_id} being updated")
            # if last_updated is within the day, update only today
            time_now = datetime.now(tzutc())
            latest_only = False
            if sprint.is_active:
                if sprint.last_updated:
                    if sprint.last_updated.date() == time_now.date():
                        latest_only = True

            from tasks.jira import (  # pylint: disable=import-outside-toplevel
                sync_sprint_issues,
            )

            result = sync_sprint_issues.delay(sprint.sprint_id, latest_only)
            result.get()

    def update(self, sprint_id) -> (List[go.Scatter], go.Layout):
        activities_subq = (
            Activity.query.filter(Activity.team_id.in_(current_user.readable_team_ids))
            .with_entities(Activity.activity_id)
            .subquery()
        )
        sprint = Sprint.query.filter(
            (Sprint.sprint_id == sprint_id) & (Sprint.activity_id.in_(activities_subq))
        ).one_or_none()
        if not sprint or sprint.is_future:
            return ([], {})

        self.check_for_data(sprint)

        index = list(
            rrule.rrule(
                rrule.DAILY,
                dtstart=sprint.start_date.date(),
                until=(sprint.complete_date or sprint.end_date).date(),
            )
        )
        index = [dt.date() for dt in index]

        return (
            self._get_plots(sprint, index),
            self._get_layout(index),
        )
