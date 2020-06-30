from datetime import datetime
from typing import List

import dash_core_components as dcc
import plotly.graph_objects as go
import sqlalchemy as sa
from dateutil.tz import tzutc
from flask import current_app

from database import db
from structure.events import Sprint, IssueSnapshot
from structure.project import StatusCategory
from structure.project import Activity  # pylint: disable=unused-import
from visuals.base import SprintVisualController


class CumulativeFlowGraphController(SprintVisualController):
    """
    Visual for showing Cumulative Flow diagram.
    """

    def __init__(self, chart_html_id: str = "cumulative-flow-diagram"):
        self.chart_html_id = chart_html_id
        self.interpolated_dates = set()

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
        # adjust index if it includes future dates
        for i in range(len(index)):
            if index[i] == datetime.now(tzutc()).date():
                index = index[: i + 1]
                break

        self.interpolated_dates = set(index)

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

        plot_list = []

        # line: status categories "To Do" and "Done"
        for status_category in [StatusCategory.done, StatusCategory.to_do]:
            q_list = (
                db.session.query(
                    sa.func.date(IssueSnapshot.snapshot_date),
                    sa.func.sum(IssueSnapshot.story_points),
                )
                .filter(
                    (IssueSnapshot.id == subquery.c.id)
                    & (IssueSnapshot.status_category == status_category)
                )
                .group_by(sa.func.date(IssueSnapshot.snapshot_date))
                .order_by(sa.func.date(IssueSnapshot.snapshot_date))
                .all()
            )
            q_dict = {k: v for k, v in q_list}
            q_y = [q_dict.get(dt) for dt in index]
            q_y[0] = q_y[0] or 0
            for idx, val in enumerate(q_y):
                if val is not None:
                    self.interpolated_dates.discard(index[idx])

            plot_list.append(
                go.Scatter(
                    name=status_category.value,
                    x=index,
                    y=q_y,
                    mode="lines",
                    stackgroup="one",
                    line_shape=(
                        "hv" if status_category == StatusCategory.to_do else "linear"
                    ),
                    stackgaps="interpolate",
                ),
            )

        # line: statuses with categories not in "To Do" or "Done"
        # unmapped statuses will fall under here
        statuses_q = (
            db.session.query(IssueSnapshot.status)
            .filter(
                ~IssueSnapshot.status_category.in_(
                    [StatusCategory.to_do, StatusCategory.done]
                )
            )
            .distinct()
            .all()
        )
        for status_obj in statuses_q:
            status = status_obj.status
            q_list = (
                db.session.query(
                    sa.func.date(IssueSnapshot.snapshot_date),
                    sa.func.sum(IssueSnapshot.story_points),
                )
                .filter(
                    (IssueSnapshot.id == subquery.c.id)
                    & (IssueSnapshot.status == status)
                )
                .group_by(sa.func.date(IssueSnapshot.snapshot_date))
                .order_by(sa.func.date(IssueSnapshot.snapshot_date))
                .all()
            )
            q_dict = {k: v for k, v in q_list}
            q_y = [q_dict.get(dt) for dt in index]
            q_y[0] = q_y[0] or 0
            for idx, val in enumerate(q_y):
                if val is not None:
                    self.interpolated_dates.discard(index[idx])

            plot_list.insert(
                1,
                go.Scatter(
                    name=status,
                    x=index,
                    y=q_y,
                    mode="lines",
                    stackgroup="one",
                    stackgaps="interpolate",
                ),
            )

        if len(self.interpolated_dates) > 0:
            current_app.logger.warning(
                f"CFD: missing data for dates: {', '.join([d.strftime('%Y-%m-%d') for d in self.interpolated_dates])}"
            )

        return plot_list

    def _get_layout(self, index: list) -> go.Layout:
        layout = super()._get_layout(index)
        layout.title.text = "Cumulative Flow"
        layout.annotations = [
            dict(x=interpolated_date, y=0, text="Missing data", showarrow=True,)
            for interpolated_date in self.interpolated_dates
        ]
        return layout
