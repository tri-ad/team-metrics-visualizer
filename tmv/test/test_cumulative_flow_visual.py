import pytest
from unittest.mock import patch
from database import db


from structure.organization import Team
from structure.events import Sprint, IssueSnapshot
from structure.project import Activity, StatusCategoryStatusMapping, StatusCategory
from visuals import CumulativeFlowGraphController
from datetime import date, datetime, timedelta


@pytest.mark.usefixtures("app")
class TestCumulativeFlowVisual:
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

    def test_cumulative_flow_update(self, mocker):
        base_date = datetime(2020, 3, 1, 5)
        _, sprint = self.setup_required_objects(base_date)

        for days in range(14):
            if days < 3:
                status = "To Do"
            elif days < 9:
                status = "In Progress"
            else:
                status = "Done"
            for hours in range(2):
                db.session.add(
                    IssueSnapshot(
                        issue_id=1,
                        story_points=1,
                        status=status,
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
        mocker.patch("visuals.CumulativeFlowGraphController.check_for_data")

        cfgc = CumulativeFlowGraphController()
        data, _ = cfgc.update(sprint.sprint_id)

        # test we have 3 lines based on setup
        assert len(data) == 3

        # test we're not getting multiple data per day
        for lines in data:
            assert len(lines.y) == len(lines.x)

        # test done is first, to-do is last for the order of stacking
        assert data[0].name == "Done"
        assert data[-1].name == "To Do"

        # test first value is never None
        for lines in data:
            assert lines.x[0] is not None

    def test_cumulative_flow_update_multiple_statuses(self, mocker):
        """
        Test that we only get one line each for "To Do" and "Done" status categories
        and one line each for all statuses of status category "In Progress"
        Data setup:
        - To Do
          - To Do
          - To Do 2
        - In Progress
          - In Progress
          - In Review
        - Done
          - Done
          - Closed
        """
        base_date = datetime(2020, 3, 1, 5)
        _, sprint = self.setup_required_objects(base_date)

        for days in range(14):
            if days < 3:
                status = "To Do"
            elif days < 6:
                status = "In Progress"
            elif days < 9:
                status = "In Review"
            elif days < 12:
                status = "Closed"
            else:
                status = "Done"
            for hours in range(2):
                db.session.add(
                    IssueSnapshot(
                        issue_id=1,
                        story_points=1,
                        status=status,
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
        mocker.patch("visuals.CumulativeFlowGraphController.check_for_data")

        cfgc = CumulativeFlowGraphController()
        data, _ = cfgc.update(sprint.sprint_id)

        # test we have 4 lines based on setup
        assert len(data) == 4

        # test we're not getting multiple data per day
        for lines in data:
            assert len(lines.y) == len(lines.x)

        # test done is first, to-do is last for the order of stacking
        assert data[0].name == "Done"
        assert data[-1].name == "To Do"

        # test first value is never None
        for lines in data:
            assert lines.x[0] is not None
