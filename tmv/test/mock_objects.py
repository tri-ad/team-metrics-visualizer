from structure.organization import Team


class UserMock:
    @property
    def readable_teams(self):
        return Team.query

    @property
    def readable_team_ids(self):
        return [team_id for team_id, in Team.query.with_entities(Team.team_id)]
