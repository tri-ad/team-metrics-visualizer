from datetime import datetime, timedelta
from enum import Enum

from dateutil.tz import tzutc
from dateutil.utils import default_tzinfo
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy import select, or_

from database import db
from structure.project import StatusCategoryStatusMapping


class Sprint(db.Model):
    class State(Enum):
        FUTURE = "future"
        ACTIVE = "active"
        CLOSED = "closed"

    __tablename__ = "sprints"

    sprint_id = db.Column(db.Integer, primary_key=True)
    activity_id = db.Column(
        db.Integer, db.ForeignKey("activities.activity_id"), nullable=False
    )

    last_updated = db.Column(db.DateTime, nullable=True)

    jira_sprint_id = db.Column(db.Integer, unique=True, nullable=True)

    name = db.Column(db.String, nullable=False)
    state = db.Column(db.String, nullable=False)
    start_date = db.Column(db.DateTime, nullable=True)
    end_date = db.Column(db.DateTime, nullable=True)
    complete_date = db.Column(db.DateTime, nullable=True)

    sp_plan = db.Column(db.Integer)

    # Set up relationship between Sprints belonging to teams
    activity = db.relationship("Activity", back_populates="sprints")
    issue_snapshots = db.relationship("IssueSnapshot", backref="sprint")

    @property
    def tz_last_updated(self):
        return default_tzinfo(self.last_updated, tzutc())

    @property
    def is_future(self):
        return self.state == self.State.FUTURE.value

    @property
    def is_active(self):
        return self.state == self.State.ACTIVE.value

    @property
    def is_closed(self):
        return self.state == self.State.CLOSED.value

    @property
    def should_be_updated(self):
        # don't update if sprint is in the future
        if self.is_future:
            return False

        # update if sprint has never been updated
        if self.last_updated is None:
            return True

        time_now = datetime.now(tzutc())
        if self.is_active:
            # update if sprint wasn't updated in the last 15 mins
            return (time_now > self.tz_last_updated) and (
                (time_now - self.tz_last_updated) > timedelta(minutes=15)
            )
        else:
            # update if sprint was last updated during the sprint
            return self.last_updated < (self.complete_date or self.end_date)


class IssueSnapshot(db.Model):
    __tablename__ = "issue_snapshots"

    id = db.Column(db.Integer, primary_key=True, nullable=False)
    sprint_id = db.Column(db.Integer, db.ForeignKey("sprints.sprint_id"), nullable=True)

    issue_id = db.Column(db.Integer, nullable=False)
    snapshot_date = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String, nullable=False)
    story_points = db.Column(
        db.Numeric(precision=5, scale=2), nullable=False, default=0
    )

    @hybrid_property
    def status_category(self):
        """
        Gets the status_category mapping based on StatusCategoryStatusMapping.
        Selected mapping is based on the ff (in order):

        1. If a matching mapping is set for Activity
        2. If a matching mapping is set by default (activity_id = None)
        3. If no match, return None
        """
        status_category_mapping = (
            StatusCategoryStatusMapping.query.filter(
                StatusCategoryStatusMapping.status == self.status,
                or_(
                    StatusCategoryStatusMapping.activity_id
                    == self.sprint.activity.activity_id,
                    StatusCategoryStatusMapping.activity_id.is_(None),
                ),
            )
            .order_by(StatusCategoryStatusMapping.activity_id.asc())
            .first()
        )
        if status_category_mapping:
            return status_category_mapping.status_category
        else:
            return None

    @status_category.expression
    def status_category(cls):  # pylint: disable=no-self-argument
        return (
            select([StatusCategoryStatusMapping.status_category])
            .where(cls.status == StatusCategoryStatusMapping.status,)
            .where(
                or_(
                    StatusCategoryStatusMapping.activity_id.in_(
                        select([Sprint.activity_id])
                        .where(cls.sprint_id == Sprint.sprint_id)
                        .as_scalar()
                    ),
                    StatusCategoryStatusMapping.activity_id.is_(None),
                )
            )
            .order_by(StatusCategoryStatusMapping.activity_id.asc())
            .limit(1)
            .as_scalar()
        )

    def __repr__(self):
        return (
            f"<Issue Snapshot: issue_id={self.issue_id} snapshot_date={self.snapshot_date} "
            f"status={self.status} story_points={self.story_points}>"
        )
