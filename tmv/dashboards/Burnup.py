from typing import List, Optional

import dash_core_components as dcc
from dash.dependencies import Input, Output
from dash.exceptions import PreventUpdate
import dash_html_components as dhtml

from dashboards import DashboardController
from visuals import Burnup, shared


class BurnupDashboardController(DashboardController):
    CHART_ID = "burnup-chart"
    TEAM_PICKER_ID = "teamPicker"
    SPRINT_PICKER_ID = "sprintPicker"

    def __init__(self):
        self.burnup_chart = Burnup.BurnupGraphController(chart_html_id=self.CHART_ID)

    def title(self):
        return "Burnup Chart"

    def dashboard(self):
        return self.standard_layout(
            controls=[
                *shared.team_and_sprint_picker(
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
        shared.callback_team_picker_state_saving(app, self.TEAM_PICKER_ID)
        shared.callback_sprint_picker_state_saving(app, self.SPRINT_PICKER_ID)

        shared.callback_update_sprints_by_team(
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
