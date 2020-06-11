import pytest
from database import db
from structure.organization import Team
from structure.project import Activity


@pytest.mark.usefixtures("app")
class TestTeamModel:
    def test_create_team_top_level(self):
        team = Team(parent_team=None, code="ABC", name="Team ABC")
        assert team is not None

        db.session.add(team)
        db.session.commit()

        # Check if the team was actually added
        assert (
            db.session.query(Team).filter(Team.code == "ABC").one_or_none() is not None
        )
