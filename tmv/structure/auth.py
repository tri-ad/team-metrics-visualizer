import enum
from datetime import datetime

from database import db
from sqlalchemy.orm import column_property
from sqlalchemy import PrimaryKeyConstraint, UniqueConstraint
from flask_security import UserMixin, RoleMixin, SQLAlchemyUserDatastore, current_user
from flask_security import AnonymousUser

from .organization import Team


class RolesUser(db.Model):
    __tablename__ = "roles_users"

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id", name="roles_users_user_id_fkey", ondelete="CASCADE"),
        index=True,
    )
    role_id = db.Column(
        db.Integer,
        db.ForeignKey("role.id", name="roles_users_role_id_fkey", ondelete="CASCADE"),
    )

    __table_args__ = (PrimaryKeyConstraint("user_id", "role_id"),)


class Role(db.Model, RoleMixin):
    __tablename__ = "role"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    description = db.Column(db.String(255), nullable=False)

    def __str__(self):
        return self.name


class CustomAnonymousUser(AnonymousUser):
    @property
    def full_name(self):
        return "Anonymous User"

    @property
    def is_superadmin(self):
        return False

    @property
    def is_dataprovider(self):
        return False

    @property
    def readable_teams(self):
        return Team.query.filter(False)

    @property
    def readable_team_ids(self):
        return self.readable_teams.with_entities(Team.team_id)

    @property
    def writable_teams(self):
        return Team.query.filter(False)

    @property
    def writable_team_ids(self):
        return self.writable_teams.with_entities(Team.team_id)


class User(db.Model, UserMixin):
    __tablename__ = "user"

    id = db.Column(db.Integer, primary_key=True)

    email = db.Column(db.String(255), unique=True, nullable=False)
    password = db.Column(db.String(255))

    first_name = db.Column(db.String(255), default="", nullable=False)
    last_name = db.Column(db.String(255), default="", nullable=False)

    last_login_at = db.Column(db.DateTime())
    current_login_at = db.Column(db.DateTime())

    last_login_ip = db.Column(db.String(100))
    current_login_ip = db.Column(db.String(100))

    login_count = db.Column(db.Integer, default=0, nullable=False)
    active = db.Column(db.Boolean(), default=True, nullable=False)

    confirmed_at = db.Column(db.DateTime())

    roles = db.relationship(
        "Role", secondary="roles_users", backref=db.backref("users", lazy="dynamic")
    )

    @property
    def full_name(self):
        full_name = f"{self.first_name} {self.last_name}".strip()

        if full_name:
            return full_name

        return self.email

    def __str__(self):
        if self.id:
            return f"#{self.id} {self.full_name}"

        return self.full_name

    @property
    def is_superadmin(self):
        return self.has_role("superadmin")

    @property
    def is_dataprovider(self):
        return self.has_role("dataprovider")

    @property
    def readable_teams(self):
        if current_user.is_superadmin:
            return Team.query

        return Team.query.filter(
            UserTeam.query.filter(
                (UserTeam.user == self) & (UserTeam.team_id == Team.team_id)
            ).exists()
        )

    @property
    def readable_team_ids(self):
        return self.readable_teams.with_entities(Team.team_id)

    @property
    def writable_teams(self):
        if current_user.is_superadmin:
            return Team.query

        return Team.query.filter(
            UserTeam.query.filter(
                (UserTeam.user == self)
                & (UserTeam.team_id == Team.team_id)
                & (UserTeam.role == TeamRoleEnum.team_admin.value)
            ).exists()
        )

    @property
    def writable_team_ids(self):
        return self.writable_teams.with_entities(Team.team_id)


class UserExternalServiceEnum(enum.Enum):
    okta = "okta"


class UserExternalService(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    user = db.relationship(User, backref="external_services")
    service = db.Column(db.String, nullable=False)  # UserExternalServiceEnum. _ .value
    service_user_id = db.Column(db.String, nullable=False)

    auth_info = db.Column(db.JSON)  # e.g. access token
    user_info = db.Column(db.JSON)

    last_used_at = db.Column(db.DateTime(), default=datetime.utcnow, nullable=False)

    __table_args__ = (
        UniqueConstraint(
            "user_id", "service", name="user_external_service_user_id_service_uniq"
        ),
        UniqueConstraint(
            "service",
            "service_user_id",
            name="user_external_service_service_service_user_id_uniq",
        ),
    )


user_datastore = SQLAlchemyUserDatastore(db, User, Role)


class TeamRoleEnum(enum.Enum):
    team_admin = "team_admin"
    member = "member"

    @property
    def title(self):
        return " ".join(i.title() for i in self.name.split("_"))


class UserTeam(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    user = db.relationship(User, backref="user_teams")

    team_id = db.Column(
        db.Integer,
        db.ForeignKey("teams.team_id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    team = db.relationship(Team, backref="user_teams")

    role = db.Column(db.String, nullable=False)  # TeamRoleEnum. _ .value

    __table_args__ = (UniqueConstraint("user_id", "team_id"),)
