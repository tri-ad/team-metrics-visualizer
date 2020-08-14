from typing import List
import pytest
from database import db
import tmv_dash_components as tdc
from test.mock_objects import UserMock
from structure.organization import Team
from slicers.organization import team_picker, department_picker, ALL_ITEMS_OPTION_ID


@pytest.fixture
def mock_user(mocker):
    mocker.patch("slicers.organization.current_user", UserMock())


@pytest.fixture
def mock_session(mocker):
    mocker.patch("slicers.state.session", dict())


@pytest.fixture
def teams(app) -> List[Team]:
    # Two departments, four teams
    # Department 1 has 3 teams
    # Department 2 has 1 team
    department1 = Team(parent_team=None, code="department1", name="Department 1")
    department2 = Team(parent_team=None, code="department2", name="Department 2")

    department1.sub_teams = [
        Team(code="11", name="Team 11"),
        Team(code="12", name="Team 12"),
        Team(code="13", name="Team 13"),
    ]
    department2.sub_teams = [Team(code="21", name="Team 21")]

    db.session.add(department1)
    db.session.add(department2)
    db.session.add_all(department1.sub_teams)
    db.session.add_all(department2.sub_teams)
    db.session.commit()

    return [department1, department2] + department1.sub_teams + department2.sub_teams


@pytest.mark.usefixtures("app", "mock_user", "mock_session")
class TestOrganizationSlicers:
    def test_team_picker(self, teams):
        picker: tdc.Dropdown = team_picker(html_element_id="testTeamPicker")[0]
        assert picker is not None
        assert picker.id == "testTeamPicker"
        assert len(picker.options) == 4
        assert len(picker.value) == 4
        for team in teams:
            if len(team.sub_teams) == 0:
                assert team.team_id in picker.value
                assert {"label": team.name, "value": team.team_id} in picker.options

    def test_team_picker_with_selection(self, teams):
        department1 = teams[0]
        team1 = department1.sub_teams[0]
        team2 = department1.sub_teams[1]

        # Multi
        picker: tdc.Dropdown = team_picker(
            selected_teams=[team1.team_id, team2.team_id]
        )[0]

        # Single
        picker_single: tdc.Dropdown = team_picker(
            selected_teams=team1.team_id, multi=False
        )[0]

        assert picker is not None
        assert len(picker.options) == 4
        assert len(picker.value) == 2
        for team in [team1, team2]:
            assert team.team_id in picker.value
            assert {"label": team.name, "value": team.team_id} in picker.options

        assert picker_single is not None
        assert len(picker_single.options) == 4
        assert picker_single.value == team1.team_id

    def test_department_picker(self, teams):
        department1, department2 = teams[0:2]
        picker: tdc.Dropdown = department_picker(
            html_element_id="testDepartmentPicker"
        )[0]
        assert picker is not None
        assert picker.id == "testDepartmentPicker"

        assert len(picker.options) == 2 + 1
        assert picker.value == ALL_ITEMS_OPTION_ID
        assert picker.options[0].get("value") == ALL_ITEMS_OPTION_ID

        for department in [department1, department2]:
            assert {
                "label": department.name,
                "value": department.team_id,
            } in picker.options

    def test_department_picker_with_selection(self, teams):
        _, department2 = teams[0:2]
        picker: tdc.Dropdown = department_picker(
            selected_department=department2.team_id
        )[0]
        assert picker is not None
        assert len(picker.options) == 2 + 1
        assert picker.value == department2.team_id
