import pytest
from typing import List, Tuple
from datetime import datetime, timedelta

from database import db

from structure.organization import Team
from structure.measurements import THCQuestion, THCMeasurement
from visuals import THCResultTableController
from visuals.team_health_check import column_id
from test.mock_objects import UserMock

# pylint: disable=too-many-locals

# THC result labels showing up in the table
GREEN = "Green"
YELLOW = "Yellow"
RED = "Red"
NO_DATA = "No data"

# THC result for three sessions
RECENT_DATE = datetime.now()
PAST_DATE = RECENT_DATE - timedelta(days=90)
LAST_YEAR_DATE = RECENT_DATE - timedelta(days=400)
RECENT = "Recent"
PAST = "Past"
LAST_YEAR = "Last year"


@pytest.fixture(scope="function")
def thc_table(db_session, mocker):
    mocker.patch("visuals.team_health_check.current_user", UserMock())

    table = THCResultTableController()
    return table


@pytest.fixture(scope="function")
def thc_data(db_session) -> Tuple[List[Team], List[THCQuestion], List[THCMeasurement]]:
    # Set up team health check test data
    # Teams
    team = Team(name="Team A", code="TeamA")  # 6 members
    teams = [team]

    # Questions
    DECK = "Test-deck"
    q1 = THCQuestion(deck=DECK, topic="Topic 1", answer_green="Good", answer_red="Bad")
    q2 = THCQuestion(deck=DECK, topic="Topic 2", answer_green="Good", answer_red="Bad")
    q_new = THCQuestion(
        deck=DECK, topic="New topic", answer_green="Great", answer_red="Oh no!"
    )
    questions = [q1, q2, q_new]

    # Clear result
    m11 = THCMeasurement(
        measurement_date=LAST_YEAR_DATE,
        session_name=LAST_YEAR,
        team=team,
        question=q1,
        result_red=0,
        result_yellow=0,
        result_green=6,
    )
    # Tie
    m12 = THCMeasurement(
        measurement_date=LAST_YEAR_DATE,
        session_name=LAST_YEAR,
        team=team,
        question=q2,
        result_red=2,
        result_yellow=2,
        result_green=2,
    )

    # One member missing
    m21 = THCMeasurement(
        measurement_date=PAST_DATE,
        session_name=PAST,
        team=team,
        question=q1,
        result_red=0,
        result_yellow=0,
        result_green=5,
    )
    # Result changed
    m22 = THCMeasurement(
        measurement_date=PAST_DATE,
        session_name=PAST,
        team=team,
        question=q2,
        result_red=1,
        result_yellow=3,
        result_green=2,
    )

    m31 = THCMeasurement(
        measurement_date=RECENT_DATE,
        session_name=RECENT,
        team=team,
        question=q1,
        result_red=0,
        result_yellow=0,
        result_green=5,
    )
    # Result changed
    m32 = THCMeasurement(
        measurement_date=RECENT_DATE,
        session_name=RECENT,
        team=team,
        question=q2,
        result_red=1,
        result_yellow=3,
        result_green=2,
    )
    # New question
    m33 = THCMeasurement(
        measurement_date=RECENT_DATE,
        session_name=RECENT,
        team=team,
        question=q_new,
        result_red=2,
        result_yellow=1,
        result_green=3,
    )
    measurements = [m11, m12, m21, m22, m31, m32, m33]

    db.session.add_all(teams)
    db.session.add_all(questions)
    db.session.add_all(measurements)
    db.session.commit()

    return teams, questions, measurements


def test_thc_table_initialized(thc_table):
    assert thc_table is not None
    assert thc_table.draw() is not None


def test_thc_default_selection(thc_data, thc_table):
    teams, _, _ = thc_data

    all_teams, session_name, compare_name = thc_table.default_selection()
    assert len(all_teams) == 1
    assert session_name == RECENT
    assert compare_name == PAST
    assert all_teams[0] == teams[0].team_id


def test_thc_result_is_correct(thc_data, thc_table):
    """
        The following is the correct result, as created by thc_data:

        +-----------+---------+---------+-----------+
        | Question  | Topic 1 | Topic 2 | New topic |
        +===========+=========+=========+===========+
        | Last year | Green   | Red     | NA        |
        | Past      | Green   | Yellow  | NA        |
        | Recent    | Green   | Yellow  | Green     |
        +-----------+---------+---------+-----------+
    """

    teams, [q1, q2, q_new], _ = thc_data
    team_id = teams[0].team_id
    team_name = teams[0].name

    # Helper-function to index into table
    def cid(session_name: str) -> str:
        return column_id(team_name, session_name)

    # PAST vs. LAST_YEAR
    _, rows = thc_table.update(team_ids=[team_id], session1=PAST, cmp_session=LAST_YEAR)
    assert len(rows) == 2
    topic1 = rows[0]
    topic2 = rows[1]
    m11 = topic1[cid(LAST_YEAR)]["text"]
    m12 = topic2[cid(LAST_YEAR)]["text"]
    m21 = topic1[cid(PAST)]["text"]
    m22 = topic2[cid(PAST)]["text"]

    # Check topic names are correct
    assert topic1["topic"]["text"] == q1.topic
    assert topic2["topic"]["text"] == q2.topic

    # Check results are correct
    assert m11 == GREEN
    assert m12 == RED
    assert m21 == GREEN
    assert m22 == YELLOW

    # RECENT vs. PAST
    _, rows = thc_table.update(team_ids=[team_id], session1=RECENT, cmp_session=PAST)
    assert len(rows) == 3
    topic1 = rows[0]
    topic2 = rows[1]
    topic3 = rows[2]
    m21 = topic1[cid(PAST)]["text"]
    m22 = topic2[cid(PAST)]["text"]
    m23 = topic3[cid(PAST)]["text"]
    m31 = topic1[cid(RECENT)]["text"]
    m32 = topic2[cid(RECENT)]["text"]
    m33 = topic3[cid(RECENT)]["text"]

    # Check topic names are correct
    assert topic1["topic"]["text"] == q1.topic
    assert topic2["topic"]["text"] == q2.topic
    assert topic3["topic"]["text"] == q_new.topic

    # Check results are correct
    assert m21 == GREEN
    assert m22 == YELLOW
    assert m23 == NO_DATA
    assert m31 == GREEN
    assert m32 == YELLOW
    assert m33 == GREEN


def test_thc_column_labels_are_correct(thc_data, thc_table):
    teams, _, _ = thc_data
    team_id = teams[0].team_id
    team_name = teams[0].name

    columns, _ = thc_table.update(team_ids=[team_id], session1=RECENT, cmp_session=PAST)
    assert len(columns) == 3
    _, session, compare = columns[:]
    assert session["headers"][0]["label"] == team_name
    assert session["headers"][1]["label"] == PAST
    assert compare["headers"][0]["label"] == team_name
    assert compare["headers"][1]["label"] == RECENT


def test_empty_result_gives_empty_table(thc_table):
    _, rows = thc_table.update(team_ids=None, session1=RECENT, cmp_session=PAST)
    assert len(rows) == 0


def test_no_data_gives_empty_default_selection(thc_table):
    teams, session, compare = thc_table.default_selection()
    assert len(teams) == 0
    assert session == ""
    assert compare == ""
