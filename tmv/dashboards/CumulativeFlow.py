from typing import List, Optional

import dash_core_components as dcc
from dash.dependencies import Input, Output
from dash.exceptions import PreventUpdate

from dashboards import DashboardController
from visuals import CumulativeFlowGraphController
import slicers


class CumulativeFlowDashboardController(DashboardController):
    CHART_ID = "cumulative-flow-diagram"
    TEAM_PICKER_ID = "team-picker-cfd"
    SPRINT_PICKER_ID = "sprint-picker-cfd"

    def __init__(self):
        self.cumulative_flow_diagram = CumulativeFlowGraphController(
            chart_html_id=self.CHART_ID
        )

    def title(self):
        return "Cumulative Flow"

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
                    id="loading-cfd",
                    children=[self.cumulative_flow_diagram.draw()],
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
        def update_cumulative_flow(selected_sprint: str) -> List[dict]:
            """
            Update CumulativeFlowGraph after sprint has selected.
            """
            if not selected_sprint:
                raise PreventUpdate
            data, layout = self.cumulative_flow_diagram.update(selected_sprint)
            return {"data": data, "layout": layout}
