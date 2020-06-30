import pytest

from database import db

from structure.measurements import OTMeasurement
from structure.organization import Team

from visuals import OvertimeChartController
from datetime import date, timedelta


@pytest.mark.usefixtures("app")
class TestOvertimeVisual:
    @pytest.fixture(scope="function")
    def ot_visual(self):
        visual = OvertimeChartController()
        return visual

    def test_visual_initialized(self, ot_visual: OvertimeChartController):
        assert ot_visual is not None

    def test_earliest_and_latest_date(self, ot_visual, mocker):
        # Create some OT measurements
        dates = (
            {date(2019, 3, 10), date(2019, 5, 5), date(2019, 5, 10)}
            | {date(2019, 8, day) for day in range(1, 32)}
            | {date(2019, 9, day) for day in range(1, 10)}
            | {date(2019, 10, 28)}
        )

        team = Team(parent_team=None, code="ABC", name="Team ABC")

        for measurement_date in dates:
            db.session.add(
                OTMeasurement(
                    measurement_date=measurement_date,
                    team=team,
                    workdays_fix=20,
                    workdays_actual=20,
                    overtime=timedelta(hours=10, minutes=15),
                )
            )
        db.session.commit()

        class UserMock:
            @property
            def readable_team_ids(self):
                return Team.query.with_entities(Team.team_id)

        mocker.patch("visuals.work_time.current_user", UserMock())

        # Check if dates in overtime chart match
        assert ot_visual.get_earliest_date() == min(dates)
        assert ot_visual.get_latest_date() == max(dates)
