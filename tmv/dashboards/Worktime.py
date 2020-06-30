from typing import List
from datetime import datetime, timedelta

from structure.organization import Team  # pylint: disable=unused-import
from dash.dependencies import Input, Output
from dashboards import DashboardController
from visuals import OvertimeChartController
import slicers


class WorktimeDashboardController(DashboardController):
    """
    Dashboard showing overtime information.
    """

    DEPARTMENT_PICKER_ID = "departmentPickerOvertime"
    TEAM_PICKER_ID = "teamPickerOvertime"
    DATE_RANGE_PICKER_ID = "datePickerRangeOvertime"
    OVERTIME_GRAPH_ID = "overtime-chart"

    def __init__(self):
        self.ot_chart = OvertimeChartController(chart_html_id=self.OVERTIME_GRAPH_ID)

    def title(self) -> str:
        return "Worktime"

    def dashboard(self) -> List:
        earliest_date = self.ot_chart.get_earliest_date()
        latest_date = self.ot_chart.get_latest_date()

        return self.standard_layout(
            controls=[
                *slicers.org.department_and_team_picker(
                    department_picker_id=self.DEPARTMENT_PICKER_ID,
                    team_picker_id=self.TEAM_PICKER_ID,
                ),
                *slicers.dates.date_range_picker(
                    html_element_id=self.DATE_RANGE_PICKER_ID,
                    display_format="YYYY/MM/DD",
                    display_format_month="MMM YYYY",
                    min_date=earliest_date,
                    max_date=latest_date + timedelta(days=1),
                    start_date=latest_date,
                    end_date=latest_date,
                ),
            ],
            visuals=[self.ot_chart.draw()],
        )

    def register_callbacks(self, app):
        slicers.org.callback_department_picker_state_saving(
            app, self.DEPARTMENT_PICKER_ID
        )
        slicers.org.callback_team_picker_state_saving(app, self.TEAM_PICKER_ID)
        slicers.dates.callback_date_range_picker_state_saving(
            app, self.DATE_RANGE_PICKER_ID
        )

        slicers.org.callback_update_teams_by_department(
            app=app,
            department_picker_id=self.DEPARTMENT_PICKER_ID,
            team_picker_id=self.TEAM_PICKER_ID,
        )

        @app.callback(
            Output(self.OVERTIME_GRAPH_ID, "figure"),
            [
                Input(self.DATE_RANGE_PICKER_ID, "start_date"),
                Input(self.DATE_RANGE_PICKER_ID, "end_date"),
                Input(self.TEAM_PICKER_ID, "value"),
            ],
        )  # pylint: disable=unused-variable
        def update_worktime_visual(
            selected_start_date: datetime,
            selected_end_date: datetime,
            selected_teams: List[int],
        ):
            traces, layout = self.ot_chart.update(
                selected_start_date, selected_end_date, selected_teams
            )
            return {"data": traces, "layout": layout}
