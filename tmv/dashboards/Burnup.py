from typing import List

import dash_core_components as dcc
from dash.dependencies import Input, Output
from dash.exceptions import PreventUpdate

from dashboards import DashboardController
from visuals import BurnupGraphController
import slicers


class BurnupDashboardController(DashboardController):
    CHART_ID = "burnup-chart"
    TEAM_PICKER_ID = "teamPicker"
    SPRINT_PICKER_ID = "sprintPicker"

    def __init__(self):
        self.burnup_chart = BurnupGraphController(chart_html_id=self.CHART_ID)

    def title(self):
        return "Burnup Chart"

    def dashboard(self):
        return self.standard_layout(
            controls=[
                *slicers.org.team_and_sprint_picker(
                    team_picker_id=self.TEAM_PICKER_ID,
                    sprint_picker_id=self.SPRINT_PICKER_ID,
                )
            ],
            visuals=[
                dcc.Loading(
                    id="loading-burnup",
                    children=[self.burnup_chart.draw()],
                    type="circle",
                )
            ],
        )

    def register_callbacks(self, app):
        slicers.org.callback_team_picker_state_saving(app, self.TEAM_PICKER_ID)
        slicers.org.callback_sprint_picker_state_saving(app, self.SPRINT_PICKER_ID)

        slicers.org.callback_update_sprints_by_team(
            app=app,
            team_picker_id=self.TEAM_PICKER_ID,
            sprint_picker_id=self.SPRINT_PICKER_ID,
        )

        @app.callback(
            Output(self.CHART_ID, "figure"), [Input(self.SPRINT_PICKER_ID, "value")]
        )  # pylint: disable=unused-variable
        def update_burnup(selected_sprint: str) -> List[dict]:
            """
            Update BurnupGraph after sprint has selected.
            """
            if not selected_sprint:
                raise PreventUpdate
            data, layout = self.burnup_chart.update(selected_sprint)
            return {"data": data, "layout": layout}
