import logging
from datetime import datetime
from typing import List, Optional

import dash
import dash_core_components as dcc
import dash_html_components as dhtml
import pandas as pd
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
from dash_bootstrap_components import Label
from flask import session
from flask_security import current_user
from sqlalchemy import or_

import tmv_dash_components as tdc
from database import db
from structure.auth import UserTeam
from structure.events import Sprint
from structure.organization import Team
from structure.project import Activity
from visuals.slicers_state import callback_slicer_state_saving, load_slicer_value

# Helper-functions


def convert_date_to_str(d):
    return d.strftime("%Y-%m-%d")


def fix_timedelta_plot(timedelta_df):
    """
    Fix the display of timedelta-values in a plotly-plot.

    Background: Plotly/dash does currently (2019/8/21) not support plotting of
    timedelta-values. When plotting values of type timedelta, plotly makes
    weird labels on the axis. A workaround is to turn them into datetime-values
    by adding the date 1970/1/1.

    Ref.: https://community.plot.ly/t/timeseries-plot-with-timedelta-axis/23560
    and: https://github.com/plotly/plotly.py/issues/801#issuecomment-317174985
    """
    return timedelta_df + pd.to_datetime("1970/1/1")


"""
    ID to use for the option "all items in a dropdown-picker.
    E.g.: All departments.
"""
ALL_ITEMS_OPTION_ID = -1

"""
    Shared Controls

    These are controls you can use in your dashboards. They provide slicing
    by common parameters like date, teams etc.
    Each of the methods below returns a List of dash-elements. It is a list
    because some controls may actually be made up of several dash elements,
    like for example the control itself and a label.
    After adding the control to your dashboard, you can connect it to your
    visuals by defining a callback in the register_callbacks()-method of your
    dashboard-class. When using the controls, be careful that you assign a
    unique html_element_id to it! If you give two controls the same id, dash
    will throw an error and your callbacks will not work.
"""


def date_picker(
    selected=datetime.today(),
    max_date=datetime.today(),
    min_date=None,
    display_format="YY/MM/DD",
    display_format_month="MMM, YY",
    html_element_id="date_picker",
) -> List:
    """
    Creates a control for selecting a single date.
    """

    picker = dcc.DatePickerSingle(
        id=html_element_id,
        max_date_allowed=max_date,
        min_date_allowed=min_date,
        initial_visible_month=selected,
        date=selected,
        first_day_of_week=1,
        display_format=display_format,
        month_format=display_format_month,
    )

    return [picker]


def date_range_picker(
    max_date=datetime.today(),
    min_date=None,
    start_date=datetime.today(),
    end_date=datetime.today(),
    display_format="YY/MM/DD",
    display_format_month="MMM, YY",
    html_element_id="date_range_picker",
) -> List:
    """
    Creates a control for selecting a range of dates.
    """

    max_date = convert_date_to_str(max_date) if max_date else None
    min_date = convert_date_to_str(min_date) if min_date else None
    start_date = convert_date_to_str(start_date) if start_date else None
    end_date = convert_date_to_str(end_date) if end_date else None

    saved_values = load_slicer_value(
        "date_range_picker",
        value_type=list,
        default=[start_date, end_date, min_date, max_date],
    )

    *_, saved_min_date, saved_max_date = saved_values

    if saved_min_date == min_date and saved_max_date == max_date:
        saved_start_date, saved_end_date, *_ = saved_values
        start_date = saved_start_date
        end_date = saved_end_date

    picker = dcc.DatePickerRange(
        id=html_element_id,
        min_date_allowed=min_date,
        max_date_allowed=max_date,
        initial_visible_month=start_date,
        start_date=start_date,
        end_date=end_date,
        first_day_of_week=1,
        display_format=display_format,
        month_format=display_format_month,
    )

    return [picker]


def callback_date_range_picker_state_saving(app, picker_id):
    callback_slicer_state_saving(
        app,
        "date_range_picker",
        picker_id,
        ["start_date", "end_date", "min_date_allowed", "max_date_allowed"],
    )


def department_and_team_picker(
    selected_department: Optional[int] = None,
    department_picker_id: str = "departmentPicker",
    selected_teams: Optional[List] = None,
    team_picker_id="teamPicker",
) -> List:
    """
    Return a dropdown for filtering by department and one for filtering by
        teams in that department.
    """

    return [
        dhtml.Div(
            id=f"{department_picker_id}_init",
            style={"display": "none"},
            **{"data-was-initialized": "0"},
        ),
        *department_picker(
            selected_department=selected_department,
            html_element_id=department_picker_id,
        ),
        *team_picker(selected_teams=selected_teams, html_element_id=team_picker_id),
    ]


def callback_update_teams_by_department(
    app, department_picker_id: str, team_picker_id: str
):
    """
    Create callback to update team-picker if department-picker was updated.
    """

    init_div_id = f"{department_picker_id}_init"

    @app.callback(
        [
            Output(team_picker_id, "options"),
            Output(team_picker_id, "value"),
            Output(init_div_id, "data-was-initialized"),
        ],
        [Input(department_picker_id, "value")],
        [State(team_picker_id, "value"), State(init_div_id, "data-was-initialized")],
    )  # pylint: disable=unused-variable
    def update_teams_by_department(
        selected_department: int, current_teams: List[int], was_initialized: str
    ):
        """ When the user switches to another department, the team-picker
            should show a list of teams in that department.
            By default, all teams in the department are selected """
        logging.debug(
            f"Worktime:update_team_picker fired with department"
            f" id={selected_department}"
        )

        # If <All departments> was selected, remove the filter (expression
        #   = True). If a specific department was selected, build a filter
        #   expression.
        if selected_department == ALL_ITEMS_OPTION_ID:
            department_filter = True
        else:
            department_filter = Team.parent_id == selected_department

        teams = (
            current_user.readable_teams.with_entities(
                Team.team_id.label("value"), Team.name.label("label")
            )
            .filter(department_filter)
            .order_by(Team.name)
            .all()
        )

        team_picker_options = [team._asdict() for team in teams]

        # Select all teams by default when switching the department.
        team_picker_selection = [team_id for team_id, name in teams]

        if was_initialized == "0":
            # if it is first callback call on component mount,
            # we should not change teams that is selected by default,
            # since we save save slicers state between dashboards
            team_picker_selection = [
                team_id for team_id in team_picker_selection if team_id in current_teams
            ]

        return team_picker_options, team_picker_selection, "1"


def callback_update_sprints_by_team(app, team_picker_id: str, sprint_picker_id: str):

    init_div_id = f"{team_picker_id}_init"

    @app.callback(
        [
            Output(sprint_picker_id, "options"),
            Output(sprint_picker_id, "value"),
            Output(init_div_id, "data-was-initialized"),
        ],
        [Input(team_picker_id, "value")],
        [State(sprint_picker_id, "value"), State(init_div_id, "data-was-initialized")],
    )  # pylint: disable=unused-variable
    def update_sprints_by_team(
        selected_team: int, current_sprint: int, was_initialized: str
    ):
        """ When the user switches to another team, the sprint-picker
            should show a list of sprints in that team.
            By default, the last sprint in the team is selected """
        logging.debug(
            f"Burnup:update_sprint_picker fired with team" f" id={selected_team}"
        )
        activities_subq = (
            Activity.query.filter(
                (Activity.team_id == selected_team)
                & (Activity.team_id.in_(current_user.readable_team_ids))
            )
            .with_entities(Activity.activity_id)
            .subquery()
        )
        sprints = (
            Sprint.query.filter(Sprint.activity_id.in_(activities_subq))
            .with_entities(Sprint.sprint_id.label("value"), Sprint.name.label("label"))
            .order_by(Sprint.start_date.desc())
            .all()
        )
        if not sprints:
            return [], None, "1"

        sprint_picker_options = [sprint._asdict() for sprint in sprints]
        # Select last sprint by default
        sprint_picker_selection = sprints[0].value

        if was_initialized == "0":
            # if it is first callback call on component mount,
            # we should not change sprint that is selected by default,
            # since we save save slicers state between dashboards
            default_value_is_valid = any(
                i["value"] == current_sprint for i in sprint_picker_options
            )
            if default_value_is_valid:
                sprint_picker_selection = current_sprint

        return sprint_picker_options, sprint_picker_selection, "1"


def department_picker(
    selected_department: Optional[int] = None, html_element_id="departmentPicker"
) -> List:
    """
    Return a dropdown for filtering by department (which is a team with
        parent-team=0)

    :param selected_department: This department is selected when the control gets
                            drawn.
    :param html_element_id: The HTML-ID for the dropdown menu created by this
                    function.
    """

    # If no department has been pre-selected, select *All departments*
    if selected_department is None:
        selected_department = ALL_ITEMS_OPTION_ID

    # Query database for a list of all departments
    departments = (
        current_user.readable_teams.with_entities(
            Team.team_id.label("value"), Team.name.label("label")
        )
        .filter(Team.parent_id == None)
        .order_by(Team.name)
        .all()
    )

    options = [{"label": "<All departments>", "value": ALL_ITEMS_OPTION_ID}]
    options.extend([department._asdict() for department in departments])

    selected_department = load_slicer_value(
        "department_picker",
        value_type=int,
        available_options=[i["value"] for i in options],
        default=selected_department,
    )

    return [
        tdc.Dropdown(
            id=html_element_id,
            label="Departments",
            options=options,
            value=selected_department,
        ),
    ]


def callback_department_picker_state_saving(app, picker_id):
    callback_slicer_state_saving(app, "department_picker", picker_id, "value")


def team_picker(
    selected_teams: Optional = None, html_element_id="teamPicker", multi: bool = True
) -> List:
    """
    Returns controls for filtering  by teams.

    :param selected_teams: You can pass a dataframe or List of team-ids to set
                            the initial selection of this control.
                            Default = None (= all teams selected)
    :param html_element_id: The HTML-ID for the dropdown menu created by this
                            function.
    :param multi: Enable multi select
    """

    # Controls for filtering by team
    # Query all teams from database
    teams = (
        current_user.readable_teams.with_entities(
            Team.team_id.label("value"), Team.name.label("label")
        )
        .order_by(Team.name)
        .all()
    )

    if selected_teams is None:
        # by default, select all if multi, select first if not multi
        if multi:
            selected_teams = [team_id for team_id, _ in teams]
        else:
            selected_teams = teams[0].value

    selected_teams = load_slicer_value(
        "team_picker",
        value_type=list if multi else int,
        available_options=[team_id for team_id, _ in teams],
        default=selected_teams,
    )

    return [
        tdc.Dropdown(
            id=html_element_id,
            label="Teams",
            options=[team._asdict() for team in teams],
            value=selected_teams,
            multi=multi,
            searchable=True,
            enableSelectAll="All Teams",
        ),
    ]


def callback_team_picker_state_saving(app, picker_id):
    callback_slicer_state_saving(app, "team_picker", picker_id, "value")


def project_picker(filter_projects: Optional = None) -> List:
    """
    Returns controls for filtering  by projects.
    """

    # Controls for filtering by activity
    if filter_projects is None:
        # Query activities from DB
        activities = (
            db.session.query(
                Activity.activity_id.label("value"),
                Activity.activity_name.label("label"),
            )
            .filter(Team.team_id.in_(current_user.writable_team_ids))
            .order_by(Activity.activity_id)
            .distinct()
            .all()
        )
    else:
        # Use only filtered projects
        activities = filter_projects

    options = [activity._asdict() for activity in activities]
    selected_value = options[0]["value"] if options else None

    selected_value = load_slicer_value(
        "project_picker",
        value_type=int,
        available_options=[i["value"] for i in options],
        default=selected_value,
    )

    return [
        tdc.Dropdown(
            id="projectPicker", label="Project", options=options, value=selected_value,
        )
    ]


def sprint_picker(
    filter_sprints: Optional = None, html_element_id: str = "sprintPicker"
) -> List:
    """
    Returns controls for filtering by sprints
    """

    # Controls for filtering by sprint
    if filter_sprints is None:
        activities_subq = (
            Activity.query.filter(Activity.team_id.in_(current_user.readable_team_ids))
            .with_entities(Activity.activity_id)
            .subquery()
        )
        sprints = (
            Sprint.query.filter(Sprint.activity_id.in_(activities_subq))
            .with_entities(Sprint.sprint_id.label("value"), Sprint.name.label("label"))
            .order_by(Sprint.start_date.desc())
            .all()
        )
    else:
        # Use only filtered projects
        sprints = filter_sprints

    options = [sprint._asdict() for sprint in sprints]
    selected_value = options[-1]["value"] if options else None

    selected_value = load_slicer_value(
        "sprint_picker",
        value_type=int,
        available_options=[i["value"] for i in options],
        default=selected_value,
    )

    return [
        tdc.Dropdown(
            id=html_element_id,
            label="Sprint",
            options=options,
            value=selected_value,
            multi=False,
        )
    ]


def callback_sprint_picker_state_saving(app, picker_id):
    callback_slicer_state_saving(app, "sprint_picker", picker_id, "value")


def team_and_sprint_picker(
    selected_teams: Optional[List] = None,
    team_picker_id="teamPicker",
    sprint_picker_id: str = "sprintPicker",
) -> List:
    """A picker to select one of team's sprints."""

    return [
        dhtml.Div(
            id=f"{team_picker_id}_init",
            style={"display": "none"},
            **{"data-was-initialized": "0"},
        ),
        *team_picker(html_element_id=team_picker_id, multi=False),
        *sprint_picker(html_element_id=sprint_picker_id),
    ]
