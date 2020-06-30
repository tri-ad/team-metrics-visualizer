from dashboards import DashboardController
from visuals import THCResultTableController, THCTrendGraphController
import slicers


class TeamHealthCheckDashboardController(DashboardController):
    DEPARTMENT_PICKER_ID = "departmentPickerTHC"
    TEAM_PICKER_ID = "teamPickerTHC"
    THC_SESSION_PICKER_ID = "thcSessionPickerTHC"
    THC_SESSION_PICKER_COMPARE_ID = "thcSessionPickerCompareTHC"
    THC_RESULT_TABLE_ID = "THCTable"
    THC_TREND_GRAPH_ID = "THCTrendGraph"

    def __init__(self):
        self.thc_table = THCResultTableController(
            table_html_id=self.THC_RESULT_TABLE_ID
        )
        self.thc_trend = THCTrendGraphController(graph_html_id=self.THC_TREND_GRAPH_ID)

    def title(self):
        return "Team Health Check"

    def dashboard(self):
        teams, session1, session2 = self.thc_table.default_selection()

        return self.standard_layout(
            controls=[
                *slicers.org.department_and_team_picker(
                    selected_teams=teams,
                    department_picker_id=self.DEPARTMENT_PICKER_ID,
                    team_picker_id=self.TEAM_PICKER_ID,
                ),
                *slicers.thc.thc_session_picker(
                    session1,
                    session2,
                    html_element_ids=(
                        self.THC_SESSION_PICKER_ID,
                        self.THC_SESSION_PICKER_COMPARE_ID,
                    ),
                ),
            ],
            visuals=[self.thc_table.draw(), self.thc_trend.draw()],
        )

    def register_callbacks(self, app):
        slicers.org.callback_department_picker_state_saving(
            app, self.DEPARTMENT_PICKER_ID
        )
        slicers.org.callback_team_picker_state_saving(app, self.TEAM_PICKER_ID)
        slicers.thc.callback_thc_session_picker_state_saving(
            app, self.THC_SESSION_PICKER_ID, self.THC_SESSION_PICKER_COMPARE_ID
        )

        slicers.org.callback_update_teams_by_department(
            app=app,
            department_picker_id=self.DEPARTMENT_PICKER_ID,
            team_picker_id=self.TEAM_PICKER_ID,
        )

        slicers.thc.callback_update_thc_visuals_by_teams_and_sessions(
            app=app,
            team_picker_id=self.TEAM_PICKER_ID,
            session_picker_id=self.THC_SESSION_PICKER_ID,
            session_picker_compare_id=self.THC_SESSION_PICKER_COMPARE_ID,
            thc_table=self.thc_table,
            thc_graph=self.thc_trend,
        )
