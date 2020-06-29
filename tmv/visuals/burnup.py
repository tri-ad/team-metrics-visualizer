import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import dash_core_components as dcc
import plotly.graph_objects as go
import sqlalchemy as sa
from dateutil.tz import tzutc
from flask_security import current_user

from connectors.jira.jira_sync import JiraSync
from database import db
from structure.events import Sprint, IssueSnapshot
from structure.project import Activity, StatusCategory
from visuals.base import SprintVisualController


class BurnupGraphController(SprintVisualController):
    """
    Visual for showing Burnup chart.
    """

    def __init__(self, chart_html_id: str = "burnup-chart"):
        self.chart_html_id = chart_html_id

    def draw(self) -> dcc.Graph:
        data, layout = self.update(sprint_id=0)

        return dcc.Graph(
            id=self.chart_html_id, figure=go.Figure(data=data, layout=layout)
        )

    def _get_plots(self, sprint: Sprint, index: list) -> List[go.Scatter]:
        """
        Get required plots for the chart.
        :param sprint: Sprint to limit issues to.
        :param index: List of dates for use in the x axis
        """
        subquery = (
            IssueSnapshot.query.distinct(
                sa.func.date(IssueSnapshot.snapshot_date), IssueSnapshot.issue_id
            )
            .filter(IssueSnapshot.sprint_id == sprint.sprint_id)
            .order_by(
                sa.func.date(IssueSnapshot.snapshot_date),
                IssueSnapshot.issue_id,
                IssueSnapshot.snapshot_date.desc(),
            )
            .subquery()
        )

        # line: sum(story points) per day
        total = (
            db.session.query(
                sa.func.date(IssueSnapshot.snapshot_date),
                sa.func.sum(IssueSnapshot.story_points).label("story_points"),
            )
            .filter(IssueSnapshot.id == subquery.c.id)
            .group_by(sa.func.date(IssueSnapshot.snapshot_date))
            .order_by(sa.func.date(IssueSnapshot.snapshot_date))
            .all()
        )
        total_dict = {k: v for k, v in total}
        total_y = [total_dict.get(dt) for dt in index]
        total_y[0] = total_y[0] or 0
        total_y[-1] = total[-1].story_points

        # line: status done story points per day
        done = (
            db.session.query(
                sa.func.date(IssueSnapshot.snapshot_date),
                sa.func.sum(IssueSnapshot.story_points),
            )
            .filter(
                (IssueSnapshot.id == subquery.c.id)
                & (IssueSnapshot.status_category == StatusCategory.done)
            )
            .group_by(sa.func.date(IssueSnapshot.snapshot_date))
            .order_by(sa.func.date(IssueSnapshot.snapshot_date))
            .all()
        )
        done_dict = {k: v for k, v in done}
        done_y = [done_dict.get(dt) for dt in index]
        done_y[0] = done_y[0] or 0

        # line: ideal burnup (start_date, 0) (end_date, scope)
        ideal_y = [0] + [None] * (len(index) - 2) + [total[-1].story_points]

        return [
            go.Scatter(
                name="Scope", x=index, y=total_y, line_shape="hv", connectgaps=True
            ),
            go.Scatter(name="Work Done", x=index, y=done_y, connectgaps=True),
            go.Scatter(name="Ideal Burnup", x=index, y=ideal_y, connectgaps=True,),
        ]

    def _get_layout(self, index: list) -> go.Layout:
        layout = super()._get_layout(index)
        layout.title.text = "Burnup Chart"
        return layout
