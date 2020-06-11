from abc import ABC
from datetime import datetime, timedelta
from structure.results import SHCResults, SP
from structure.events import Sprint
from structure.project import Activity
from functools import total_ordering

from enum import Enum
from sqlalchemy.dialects.postgresql import UUID
from uuid import uuid4
from database import db

# OVERTIME
###
# Measurement for overtime


class OTMeasurement(db.Model):
    """
    This is a measurement of overtime for one member in a specific month.
    The overtime is always the accumulated overtime in the month of
    `measurement_date`.
    """

    __tablename__ = "m_overtime"

    # Primary key
    pk = db.Column(db.Integer, primary_key=True)
    # UUID for measurement
    measurement_id = db.Column(
        UUID(as_uuid=True), unique=True, nullable=False, default=uuid4
    )
    # Date of measurement
    measurement_date = db.Column(db.Date, nullable=False)
    # Team ID
    team_id = db.Column(db.Integer, db.ForeignKey("teams.team_id"))
    # Relationship to team
    team = db.relationship("Team")

    # Days to work & actual worked
    workdays_fix = db.Column(db.Integer)
    workdays_actual = db.Column(db.Integer, nullable=False)

    # Overtime is assumed to be measured cumulative
    #   for the month of measurement_date
    overtime = db.Column(db.Interval)

    def year(self):
        return self.measurement_date.year

    def month(self):
        return self.measurement_date.month

    def period(self):
        """
        Return identifier of period for this measurement
        as YYYY/MM.
        Ex.: 2019/05
        """
        return f"{self.measurement_date.year}/{self.measurement_date.month}"

    def __repr__(self):
        return (
            f"<OTMeasurement: "
            f"measurement_id={self.measurement_id}, "
            f"measurement_date={self.measurement_date}"
            f", team_id={self.team_id}"
            f", workdays_fix={self.workdays_fix}"
            f", workdays_actual={self.workdays_actual}"
            f", overtime={self.overtime}"
            ">"
        )


# TEAM HEALTH CHECK
###
# Result of Team Health Check
@total_ordering
class THCResult(Enum):
    """
    Datatype for Team Health Check result of one question.
    This class allows to compare two results (e.g. from two sessions) of THC
    with each other using the regular operators "<", ">" etc.

    The total ordering is: Red < Yellow < Green

    NoResult is used in case there was no answer on the question. It is treated
    as a separate case in the UI but compares as: NoResult < Red.
    """

    Red = 1
    Yellow = 2
    Green = 3
    NoResult = 0

    def __lt__(self, other):
        if self.__class__ is other.__class__:
            return self.value < other.value
        return NotImplemented


def thc_final_result(nr_red: int, nr_yellow: int, nr_green: int) -> THCResult:
    """
    Converts measurement from Team Health Check to a final result.
    Logic: Category with maximum number of votes wins. If there is a tie,
    the worse category wins.

    Example (R/Y/G):

    +---+---+---+--------+
    | R | Y | G | Result |
    +===+===+===+========+
    | 2 | 2 | 4 | Green  |
    +---+---+---+--------+
    | 3 | 2 | 3 | Red    |
    +---+---+---+--------+

    :param nr_red: Number of votes for red.
    :param nr_yellow: Number of votes for yellow.
    :param nr_green: Number of votes for green.
    :return: Final result as THCResult.
    """
    all_results = {nr_red, nr_yellow, nr_green}
    if max(all_results) == nr_red:
        return THCResult.Red
    elif max(all_results) == nr_yellow:
        return THCResult.Yellow
    else:
        return THCResult.Green


class THCQuestion(db.Model):
    """
    Used to store questions/topics for Team Health Check sessions.

    Example:

    +--------------+------------------------------------------------------+
    | deck         | Spotify original                                     |
    +--------------+------------------------------------------------------+
    | topic        | Teamwork                                             |
    +--------------+------------------------------------------------------+
    | answer_green | I feel we often collaborate closely with each other  |
    |              | toward common goals.                                 |
    +--------------+------------------------------------------------------+
    | answer_red   | We work individually, and care little about what the |
    |              | others are doing.                                    |
    +--------------+------------------------------------------------------+
    """

    __tablename__ = "res_thc_questions"

    question_id = db.Column(db.Integer, primary_key=True)
    # This allows us to organize questions into different decks, like folders
    deck = db.Column(db.String)
    # The topic of the question, e.g.: "Teamwork", "Health of codebase", etc.
    topic = db.Column(db.String, unique=True, nullable=False)
    # `answer_green` is the perfect situation, `answer_red` is the worst case
    answer_green = db.Column(db.String)
    answer_red = db.Column(db.String)

    def __repr__(self):
        return "<THCQuestion: question_id={}, deck={}, topic={}, answer_green={}, answer_red={}>".format(
            self.question_id, self.deck, self.topic, self.answer_green, self.answer_red
        )

    def __str__(self):
        return f"{self.deck}: {self.topic}"


# Measurement for Team Health Check
class THCMeasurement(db.Model):
    """
    THCMeasurement stores the number of answers for red, yellow and green for
    one question asked to one team in one session of Team Health Check.
    A whole session of Team Health Check done with one team would therefore
    produce several of these measurements - one for each question.
    """

    __tablename__ = "m_thc"

    # Primary key
    pk = db.Column(db.Integer, primary_key=True)
    # UUID for measurement
    measurement_id = db.Column(
        UUID(as_uuid=True), unique=True, nullable=False, default=uuid4
    )
    # Date of measurement
    measurement_date = db.Column(db.DateTime, nullable=False)
    # Name of the session (to group with other team's results)
    session_name = db.Column(db.String, nullable=False)
    # Team and question ID
    team_id = db.Column(db.Integer, db.ForeignKey("teams.team_id"))
    question_id = db.Column(db.Integer, db.ForeignKey("res_thc_questions.question_id"))
    # Result
    result_red = db.Column(db.Integer)
    result_yellow = db.Column(db.Integer)
    result_green = db.Column(db.Integer)

    # Relationship to team
    team = db.relationship("Team")

    # Relationship to question
    question = db.relationship("THCQuestion")

    # The triple (session, team, question) makes the measurement unique:
    __table_args__ = (db.UniqueConstraint(session_name, team_id, question_id),)

    def __repr__(self):
        return (
            "<THCMeasurement: measurement_id={}, measurement_date={}, session_name={}, team_id={}, "
            "question_id={}, result_red={}, result_yellow={}, result_green={}>".format(
                self.measurement_id,
                self.measurement_date,
                self.session_name,
                self.team_id,
                self.question_id,
                self.result_red,
                self.result_yellow,
                self.result_green,
            )
        )


# BURNDOWN
###
class BurndownMeasurement(db.Model):
    __tablename__ = "m_burndown"

    pk = db.Column(db.Integer, primary_key=True)
    measurement_id = db.Column(
        UUID(as_uuid=True), unique=True, nullable=False, default=uuid4
    )
    measurement_date = db.Column(db.DateTime, nullable=False)
    activity_id = db.Column(db.Integer, db.ForeignKey("activities.activity_id"))
    sprint_id = db.Column(db.Integer, db.ForeignKey("sprints.sprint_id"))

    sp_not_done = db.Column(db.Integer)
    sp_added = db.Column(db.Integer, default=0)
    sp_swapped = db.Column(db.Integer, default=0)

    # Relationship to sprint
    sprint = db.relationship("Sprint")
    # Relationship to activity
    activity = db.relationship("Activity")

    # TODO: Relationship to team

    # A burndown-measurement is unique per sprint and measurement datetime
    __table_args__ = (db.UniqueConstraint(measurement_date, sprint_id),)

    def __repr__(self):
        return (
            "<BurndownMeasurement: measurement_id={}, measurement_date={}, sprint_id={}, "
            "sp_not_done={}, sp_added={}, sp_swapped={}".format(
                self.measurement_id,
                self.measurement_date,
                self.sprint_id,
                self.sp_not_done,
                self.sp_added,
                self.sp_swapped,
            )
        )


"""
TODO: Add class for Cumulative-Flow measurement
    sprint
    sp_todo
    sp_in_progress
    sp_done

"""
