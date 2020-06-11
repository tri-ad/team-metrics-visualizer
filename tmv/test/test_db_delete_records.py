import pytest
from tools.db_tool import action_delete_all_for_model

from database import db

from structure.organization import Team


@pytest.mark.usefixtures("app")
class TestDbDeleteRecords:
    def test_delete_records_team(self, db_session):
        # Create some records in the database
        for i in range(5):
            db.session.add(Team(code=str(i), name=f"Team {i}", parent_team=None))
        db.session.commit()

        # Delete records
        success = action_delete_all_for_model(model_name="Team", output=print)

        # Assert DB has no records in it for model
        assert db.session.query(Team).count() == 0
        # Assert function returned True
        assert success

    def test_delete_records_fail_on_unsupported_model(self):
        # Try to delete records for unsupported model
        success = action_delete_all_for_model(model_name="I_do_not_exist", output=print)
        assert not success
