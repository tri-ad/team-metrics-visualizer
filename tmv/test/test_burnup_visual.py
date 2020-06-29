import pytest
from unittest.mock import patch
from database import db

from common.utils import create_default_status_mappings
from structure.organization import Team
from structure.events import Sprint, IssueSnapshot
from structure.project import Activity, StatusCategory, StatusCategoryStatusMapping
from visuals import BurnupGraphController
from datetime import date, datetime, timedelta


@pytest.mark.usefixtures("app")
class TestBurnupVisual:
    def setup_required_objects(self, base_date: datetime):
        team = Team(parent_team=None, code="ABC", name="Team ABC")
        db.session.add(team)
        db.session.commit()

        activity = Activity(team_id=team.team_id, activity_name="ABC")
        db.session.add(activity)
        db.session.commit()

        sprint = Sprint(
            activity_id=activity.activity_id,
            last_updated=datetime(2020, 4, 5, 6),
            name="ABC 1",
            state=Sprint.State.CLOSED.value,
            start_date=base_date,
            end_date=base_date + timedelta(days=13),
            complete_date=base_date + timedelta(days=13),
        )
        db.session.add(sprint)
        db.session.commit()

        status_mapping_dict = {
            "To Do": "To Do",
            "In Progress": "In Progress",
            "In Review": "In Progress",
            "Done": "Done",
            "Closed": "Done",
        }
        for status, status_category_str in status_mapping_dict.items():
            status_category = StatusCategory(status_category_str)
            status_mapping_obj = StatusCategoryStatusMapping(
                status=status, status_category=status_category
            )
            db.session.add(status_mapping_obj)
        db.session.commit()
        return activity, sprint

    def test_burnup_update(self, mocker):
        base_date = datetime(2020, 3, 1, 5)
        _, sprint = self.setup_required_objects(base_date)

        for days in range(14):
            for hours in range(2):
                db.session.add(
                    IssueSnapshot(
                        issue_id=1,
                        story_points=1,
                        status="Done",
                        sprint_id=sprint.sprint_id,
                        snapshot_date=(base_date + timedelta(days=days))
                        - timedelta(hours=hours),
                    )
                )
        db.session.commit()

        class UserMock:
            @property
            def readable_team_ids(self):
                return Team.query.with_entities(Team.team_id)

        mocker.patch("visuals.base.current_user", UserMock())
        mocker.patch("visuals.BurnupGraphController.check_for_data")

        bgc = BurnupGraphController()
        data, _ = bgc.update(sprint.sprint_id)
        scope, work_done, ideal = data

        # test we're not getting multiple data per day
        assert len(work_done.y) == len(work_done.x)
        assert len(scope.y) == len(scope.x)
        assert scope.y[-1] == ideal.y[-1]
        assert ideal.y[0] == 0
        for i in work_done.y:
            assert i == 1
        for i in ideal.y[1:-1]:
            assert i == None
