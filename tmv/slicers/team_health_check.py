from typing import Optional, Tuple, List
import pandas as pd
import plotly.graph_objects as go
from dash.dependencies import Input, Output
from flask_security import current_user

from database import db
from sqlalchemy import func, desc
from structure.organization import Team
from structure.measurements import THCMeasurement

from dash_bootstrap_components import ButtonGroup
import tmv_dash_components as tdc
from slicers import state


def callback_thc_session_picker_state_saving(app, picker_id, picker_compare_id):
    state.callback_slicer_state_saving(app, "thc_session_picker_0", picker_id, "value")
    state.callback_slicer_state_saving(
        app, "thc_session_picker_1", picker_compare_id, "value"
    )


def callback_update_thc_visuals_by_teams_and_sessions(
    app,
    team_picker_id: str,
    session_picker_id: str,
    session_picker_compare_id: str,
    thc_table: Optional = None,  # THCResultTableController
    thc_graph_id: str = "",
    thc_graph: Optional = None,  # THCTrendGraphController
):
    # Configure outputs based on which visuals are in the dashboard
    outputs = []
    if thc_table is not None:
        thc_table_id = thc_table.table_html_id
        outputs += [
            Output(thc_table_id, "columns"),
            Output(thc_table_id, "data"),
        ]

    if thc_graph is not None:
        thc_graph_id = thc_graph.graph_html_id
        outputs += [Output(thc_graph_id, "figure")]

    @app.callback(
        outputs,
        [
            Input(team_picker_id, "value"),
            Input(session_picker_id, "value"),
            Input(session_picker_compare_id, "value"),
        ],
    )  # pylint: disable=unused-variable
    def update_thc_visuals_by_teams_and_sessions(
        selected_teams: List[int], selected_session1: str, selected_cmp_session: str
    ):
        """
        Update THC result after teams and/or selected session has changed.
        """

        output_data = []

        # Call update-function to get new columns and data for table
        if thc_table is not None:
            cols, rows = thc_table.update(
                selected_teams, selected_session1, selected_cmp_session
            )
            output_data += [cols, rows]

        if thc_graph is not None:
            try:
                selected_team = selected_teams[0]
            except IndexError:
                selected_team = 0
                data = []
                layout = dict()
            else:
                data, layout = thc_graph.update(team_id=selected_team)

            output_data += [go.Figure(data=data, layout=layout)]

        # TODO: Update selector2, so that you cannot select same value in both selectors.

        return output_data


def thc_session_picker(
    selected_session1: str,
    selected_cmp_session: str,
    html_element_ids: Tuple = ("session1Picker", "cmpSessionPicker"),
) -> List:
    """
    Returns controls for filtering THC table by sessions.
    """
    # Init controls list and DB session
    controls = []
    selected_sessions = (selected_session1, selected_cmp_session)

    # Query sessions from DB & add min-/max date for measurement
    sessions = pd.read_sql(
        db.session.query(
            THCMeasurement.session_name.label("session"),
            func.min(THCMeasurement.measurement_date).label("min_date"),
            func.max(THCMeasurement.measurement_date).label("max_date"),
        )
        .filter(Team.team_id.in_(current_user.readable_team_ids))
        .group_by(THCMeasurement.session_name)
        .order_by(desc("min_date"))  # Order sessions from newest to oldest
        .statement,
        db.session.bind,
    )

    # Add controls to list
    def __session_dropdown_label(row) -> str:
        """
        Creates label for the session dropdown given a row
        from the DataFrame containing the sessions
        """
        d_min = row["min_date"]
        d_max = row["max_date"]

        try:
            if d_min.month == d_max.month and d_min.year == d_max.year:
                d1 = d_min.strftime("%b/%d")
                d2 = d_max.strftime("%d")
            else:
                d1 = d_min.strftime("%Y/%b")
                d2 = d_max.strftime("%b")

            return f"{row['session']} ({d1}~{d2})"
        except AttributeError:
            return f"{row['session']}"

    options = [
        {"label": __session_dropdown_label(row), "value": row["session"]}
        for _, row in sessions.iterrows()
    ]

    for control_i in [0, 1]:
        selected_value = selected_sessions[control_i]

        selected_value = state.load_slicer_value(
            f"thc_session_picker_{control_i}",
            value_type=str,
            available_options=[i["value"] for i in options],
            default=selected_value,
        )

        controls.append(
            tdc.Dropdown(
                id=html_element_ids[control_i],
                labelPrefix="Compare to" if control_i == 1 else "",
                label="Session",
                options=options,
                value=selected_value,
            )
        )

    return [ButtonGroup(controls)]
