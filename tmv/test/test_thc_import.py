import pytest
from test import TEST_RESOURCES_DIRECTORY

from database import db
from tools.db_tool import action_import_thc_questions
from connectors.TeamHealthCheck.thc_import import THCImporter
from structure.measurements import THCQuestion, THCMeasurement
from structure.organization import Team


@pytest.mark.usefixtures("app")
class TestTHCImport:
    TEST_FILE_QUESTIONS = TEST_RESOURCES_DIRECTORY / "thc_questions_test_data.txt"
    TEST_FILE_RESULT = TEST_RESOURCES_DIRECTORY / "thc_result_test_data.xlsx"

    TEST_FILE_THC_NICE = TEST_RESOURCES_DIRECTORY / "thc_result_test_data.xlsx"
    TEST_FILE_THC_UNKNOWN_QUESTION = (
        TEST_RESOURCES_DIRECTORY / "thc_result_test_data_with_unknown_question.xlsx"
    )
    TEST_FILE_THC_NO_ANSWER_ON_ONE_QUESTION = (
        TEST_RESOURCES_DIRECTORY / "thc_result_no_answer_on_one_question.xlsx"
    )

    def import_questions(self):
        action_import_thc_questions(TestTHCImport.TEST_FILE_QUESTIONS, output=print)

    def test_import_questions(self):
        self.import_questions()

        result_one = (
            db.session.query(THCQuestion)
            .filter(THCQuestion.topic == "Trust & Safety")
            .first()
        )

        assert result_one is not None
        assert (
            result_one.answer_green.strip()
            == "I feel safe to be myself and to share my thoughts. We don't hesitate to engage in constructive conflicts."
        )
        assert (
            result_one.answer_red.strip()
            == "Mistakes and failures are not accepted. I don't feel safe to speak up in meetings. We avoid constructive conflicts."
        )

        result_count = db.session.query(THCQuestion).count()
        assert result_count is not None
        assert result_count == 4

    def add_teams(self):
        team_names = {"Team A", "Team B", "Team C", "Team D"}
        for team_name in team_names:
            db.session.add(Team(parent_team=None, name=team_name, code=team_name))
        db.session.commit()

    def test_import_thc_result(self):
        # Import a nicely formatted thc result
        self.import_questions()
        self.add_teams()

        # Import result and check that everything was added to the db
        importer = THCImporter(file_name=TestTHCImport.TEST_FILE_THC_NICE)
        assert importer is not None
        importer.process()
        importer.commit()

        # There should overall be six measurements with three topics
        assert db.session.query(THCMeasurement).count() == 6 * 4
        assert (
            db.session.query(THCMeasurement)
            .join(THCQuestion)
            .join(Team)
            .filter(Team.name == "Team C", THCQuestion.topic == "Trust & Safety")
            .count()
            == 2
        )
        assert (
            db.session.query(THCMeasurement)
            .join(THCQuestion)
            .join(Team)
            .filter(Team.name == "Team D", THCQuestion.topic == "Trust & Safety")
            .count()
            == 1
        )

        # Check one specific entry
        result = (
            db.session.query(THCMeasurement)
            .join(THCQuestion)
            .join(Team)
            .filter(
                Team.name == "Team B",
                THCMeasurement.session_name == "2019 Q3S",
                THCQuestion.topic == "Purpose",
            )
            .one_or_none()
        )
        assert result is not None
        measurement_date = result.measurement_date
        assert measurement_date.year == 2019
        assert measurement_date.month == 7
        assert measurement_date.day == 22
        assert result.result_red == 1
        assert result.result_yellow == 3
        assert result.result_green == 2

    def test_import_thc_result_unknown_question(self):
        # Import a THC result with one question too much
        self.import_questions()
        self.add_teams()

        importer = THCImporter(file_name=TestTHCImport.TEST_FILE_THC_UNKNOWN_QUESTION,)
        assert importer is not None
        importer.process()
        importer.commit()

        assert db.session.query(THCMeasurement).count() == 6 * 4
        assert (
            db.session.query(THCMeasurement)
            .join(THCQuestion)
            .filter(THCQuestion.topic == "Team Autonomy")
            .one_or_none()
            is None
        )

    def test_import_thc_result_no_answer(self):
        self.import_questions()
        self.add_teams()

        importer = THCImporter(
            file_name=TestTHCImport.TEST_FILE_THC_NO_ANSWER_ON_ONE_QUESTION,
        )
        assert importer is not None
        importer.process()
        importer.commit()

        assert db.session.query(THCMeasurement).count() == 4 - 1
        assert (
            db.session.query(THCMeasurement)
            .join(THCQuestion)
            .filter(THCQuestion.topic == "Dependability")
            .one_or_none()
            is None
        )
