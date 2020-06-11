import pytest
from database import db
from structure.project import Activity, JiraProject


@pytest.mark.usefixtures("app")
class TestProjectModels:
    def test_create_activity_no_project(self, team):
        activity = Activity(team_id=team.team_id, activity_name="ABC Activity")

        db.session.add(activity)
        db.session.commit()

        # Check if activity was added
        assert (
            db.session.query(Activity)
            .filter(Activity.activity_name == "ABC Activity")
            .one_or_none()
            is not None
        )

    def test_create_activity_with_project(self, team):
        project = JiraProject(project_key="TP-1", project_name="Test Project 1")
        assert project is not None

        db.session.add(project)
        db.session.commit()

        assert (
            db.session.query(JiraProject)
            .filter(JiraProject.project_key == "TP-1")
            .one_or_none()
            is not None
        )

        activity = Activity(
            team_id=team.team_id,
            activity_name="ABC Activity",
            jira_project_id=project.id,
        )

        db.session.add(activity)
        db.session.commit()

        # Check if activity was added
        assert (
            db.session.query(Activity)
            .filter(Activity.activity_name == "ABC Activity")
            .filter(Activity.jira_project.has(project_key="TP-1"))
            .one_or_none()
            is not None
        )
