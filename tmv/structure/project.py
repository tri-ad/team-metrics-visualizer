import enum
from database import db


class StatusCategory(enum.Enum):
    to_do = "To Do"
    in_progress = "In Progress"
    done = "Done"


class Activity(db.Model):
    __tablename__ = "activities"

    activity_id = db.Column(db.Integer, primary_key=True)
    team_id = db.Column(db.Integer, db.ForeignKey("teams.team_id"))

    activity_name = db.Column(db.String, unique=True)
    jira_project_id = db.Column(db.Integer, db.ForeignKey("jira_projects.id"))

    sprints = db.relationship("Sprint", back_populates="activity")
    # Set up relationship between Sprints belonging to teams
    team = db.relationship("Team", back_populates="activities")

    def __repr__(self):
        return "<Activity: activity_id={}, activity_name={} jira_project_id={}>".format(
            self.activity_id, self.activity_name, self.jira_project_id
        )


class JiraProject(db.Model):
    __tablename__ = "jira_projects"

    id = db.Column(db.Integer, primary_key=True, nullable=False)
    project_key = db.Column(db.String, unique=True, nullable=False)
    project_name = db.Column(db.String, nullable=False)

    activity = db.relationship("Activity", backref="jira_project", uselist=False)

    def __repr__(self):
        return f"<JIRA Project: id={self.id}, project_key={self.project_key}, project_name={self.project_name}>"

    def __str__(self):
        return f"{self.project_name} ({self.project_key})"


class StatusCategoryStatusMapping(db.Model):
    __tablename__ = "status_category_status_mappings"

    id = db.Column(db.Integer, primary_key=True, nullable=False)
    activity_id = db.Column(
        db.Integer, db.ForeignKey("activities.activity_id"), nullable=True
    )
    status = db.Column(db.String, nullable=False)
    status_category = db.Column(db.Enum(StatusCategory), nullable=False)

    activity = db.relationship("Activity", backref="status_mappings")

    __table_args__ = (
        db.UniqueConstraint("activity_id", "status"),
        db.Index(
            "ix_status_activity_id_null",
            "status",
            unique=True,
            postgresql_where=(activity_id.is_(None)),
        ),
    )
