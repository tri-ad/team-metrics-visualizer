from database import db


class Team(db.Model):
    __tablename__ = "teams"

    team_id = db.Column(db.Integer, primary_key=True)
    parent_id = db.Column(db.Integer, db.ForeignKey("teams.team_id"))
    # Unique code / name for the team.
    code = db.Column(db.String, nullable=False, unique=True)
    # This name will be displayed in visuals, controls, etc.
    name = db.Column(db.String, nullable=False)

    # Set up relationship between teams of higher and lower level
    sub_teams = db.relationship(
        "Team", backref=db.backref("parent_team", remote_side=[team_id])
    )

    # Set up relationship between Activities belonging to teams
    activities = db.relationship("Activity", back_populates="team")

    def __repr__(self):
        return "<Team: team_id={}, parent_id={}, code={}, name={}>".format(
            self.team_id, self.parent_id, self.code, self.name
        )

    def __str__(self):
        return f"{self.name} ({self.code})"
