import logging
from typing import List
from datetime import timedelta, datetime
import dash_html_components as dhtml
from dash.dependencies import Input, Output
from dashboards.base import DashboardController
from visuals import shared
from visuals import THCResultTableController, OvertimeChartController
from visuals import TeamHealthCheck


class LongTermHealthDashboardController(DashboardController):
    """ A dashboard showing team health over several months """

    DATE_RANGE_PICKER_ID = "datePickerRangeTeamHealth"
    DEPARTMENT_PICKER_ID = "departmentPickerHealth"
    TEAM_PICKER_ID = "teamPickerHealth"
    THC_SESSION_PICKER_ID = "thcSessionPickerHealth"
    THC_SESSION_PICKER_COMPARE_ID = "thcSessionPickerCompareHealth"

    THC_RESULT_TABLE_ID = "THCTableLongTerm"
    OVERTIME_GRAPH_ID = "OTChartLongTerm"

    def __init__(self):
        self.thc_table = THCResultTableController(
            table_html_id=self.THC_RESULT_TABLE_ID
        )
        self.ot_chart = OvertimeChartController(chart_html_id=self.OVERTIME_GRAPH_ID)

    def title(self) -> str:
        return "Team health"

    def dashboard(self) -> List:
        ot_earliest_date = self.ot_chart.get_earliest_date()
        ot_latest_date = self.ot_chart.get_latest_date()
        (_, default_session, default_compare) = self.thc_table.default_selection()

        return self.standard_grid_layout(
            controls=[
                *shared.department_and_team_picker(
                    department_picker_id=self.DEPARTMENT_PICKER_ID,
                    team_picker_id=self.TEAM_PICKER_ID,
                ),
                *shared.date_range_picker(
                    html_element_id=self.DATE_RANGE_PICKER_ID,
                    display_format="YYYY/MM/DD",
                    display_format_month="MMM YYYY",
                    min_date=ot_earliest_date,
                    max_date=ot_latest_date + timedelta(days=1),
                    start_date=ot_latest_date,
                    end_date=ot_latest_date,
                ),
                dhtml.Br(),
                *TeamHealthCheck.thc_session_picker(
                    default_session,
                    default_compare,
                    html_element_ids=(
                        self.THC_SESSION_PICKER_ID,
                        self.THC_SESSION_PICKER_COMPARE_ID,
                    ),
                ),
            ],
            visuals=[self.ot_chart.draw(), self.thc_table.draw()],
        )

    def register_callbacks(self, app):
        shared.callback_department_picker_state_saving(app, self.DEPARTMENT_PICKER_ID)
        shared.callback_team_picker_state_saving(app, self.TEAM_PICKER_ID)
        TeamHealthCheck.callback_thc_session_picker_state_saving(
            app, self.THC_SESSION_PICKER_ID, self.THC_SESSION_PICKER_COMPARE_ID
        )
        shared.callback_date_range_picker_state_saving(app, self.DATE_RANGE_PICKER_ID)

        shared.callback_update_teams_by_department(
            app=app,
            department_picker_id=self.DEPARTMENT_PICKER_ID,
            team_picker_id=self.TEAM_PICKER_ID,
        )

        TeamHealthCheck.callback_update_thc_visuals_by_teams_and_sessions(
            app=app,
            team_picker_id=self.TEAM_PICKER_ID,
            session_picker_id=self.THC_SESSION_PICKER_ID,
            session_picker_compare_id=self.THC_SESSION_PICKER_COMPARE_ID,
            thc_table=self.thc_table,
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
