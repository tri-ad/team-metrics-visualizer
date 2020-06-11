import pytest
from test import TEST_RESOURCES_DIRECTORY

from datetime import date, timedelta
from database import db
from structure.organization import Team
from structure.measurements import OTMeasurement
from tools.db_tool import action_process_overtime_data, action_commit_overtime_data


@pytest.mark.usefixtures("app")
class TestOTImporter:
    TEST_FILE_NICE = TEST_RESOURCES_DIRECTORY / "overtime_test_data.xlsx"
    TEST_FILE_STRANGE_SHEET_NAME = (
        TEST_RESOURCES_DIRECTORY / "overtime_test_data_strange_sheet_name.xlsx"
    )
    TEST_FILE_WRONG_FORMAT = TEST_RESOURCES_DIRECTORY / "overtime_WrongFormat.xlsx"

    def add_teams(self):
        department = Team(parent_team=None, name="Department", code="Dptmnt")
        db.session.add(department)

        team_codes_and_names = {
            "CodeA": "Team A",
            "CodeB": "Team B",
            "CodeNameChange": "Team with name change",
            "CodeOneMember": "Team with only one member",
        }
        for code, name in team_codes_and_names.items():
            db.session.add(Team(parent_team=department, name=name, code=code))
        db.session.commit()

    def test_import_overtime_result(self):
        self.add_teams()

        importer = action_process_overtime_data(
            TestOTImporter.TEST_FILE_NICE, output=print
        )
        assert importer is not None

        action_commit_overtime_data(importer, output=print)
        assert db.session.query(OTMeasurement).first() is not None

        # Team A had three members in August and only Team A's result was
        # measured
        assert (
            db.session.query(OTMeasurement)
            .filter(
                OTMeasurement.measurement_date.between(
                    date(2019, 8, 1), date(2019, 8, 31)
                )
            )
            .count()
            == 3
        )
        assert (
            db.session.query(OTMeasurement)
            .join(Team)
            .filter(
                OTMeasurement.measurement_date.between(
                    date(2019, 8, 1), date(2019, 8, 31)
                ),
                Team.code == "CodeA",
            )
            .count()
            == 3
        )

        """ Check this specific record in 2019/04
        Code	Team	    Function	Overtime	Fixed Working days	Actual working days
        CodeB	Department	Team B	    73: 29	    22	                22
        """
        result = (
            db.session.query(OTMeasurement)
            .join(Team)
            .filter(
                Team.code == "CodeB",
                OTMeasurement.measurement_date.between(
                    date(2019, 4, 1), date(2019, 4, 30)
                ),
                OTMeasurement.overtime == timedelta(hours=73, minutes=29),
            )
            .one_or_none()
        )
        assert result is not None
        assert result.workdays_fix == 22
        assert result.workdays_actual == 22

        # Check correct number of records inserted
        assert (
            db.session.query(OTMeasurement)
            .filter(
                OTMeasurement.measurement_date.between(
                    date(2019, 3, 1), date(2019, 3, 31)
                )
            )
            .count()
            == 24
        )

    def test_strange_sheet_name(self):
        # Tries to import a file with wrongly formatted sheet names.
        # This should not import any data to the database.
        self.add_teams()

        importer = action_process_overtime_data(
            TestOTImporter.TEST_FILE_STRANGE_SHEET_NAME, output=print,
        )
        assert importer is not None

        action_commit_overtime_data(importer, output=print)

        assert db.session.query(OTMeasurement).count() == 0

    def test_GivenWrongOvertimeFormat_ShouldCastToCorrectFormat(self):
        self.add_teams()

        importer = action_process_overtime_data(
            TestOTImporter.TEST_FILE_WRONG_FORMAT, output=print
        )
        action_commit_overtime_data(importer, output=print)

        assert db.session.query(OTMeasurement).count() == 2

        result = db.session.query(OTMeasurement).all()
        assert result[0].overtime == timedelta(hours=-13, minutes=-15)
        assert result[1].overtime == timedelta(hours=25, minutes=4)
