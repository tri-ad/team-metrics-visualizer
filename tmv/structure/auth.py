import enum
from collections import defaultdict, namedtuple
from datetime import datetime

from flask_security import (
    AnonymousUser,
    RoleMixin,
    SQLAlchemyUserDatastore,
    UserMixin,
)
from sqlalchemy import PrimaryKeyConstraint, UniqueConstraint, text
from sqlalchemy.orm import column_property

from database import db

from structure.organization import Team


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
        """User can read team's data"""
        if self.is_superadmin:
            return Team.query

        return Team.query.filter(Team.team_id.in_(self.readable_team_ids))

    @property
    def readable_team_ids(self):
        """User can read team's data"""
        if self.is_superadmin:
            return [team_id for team_id, in Team.query.with_entities(Team.team_id)]

        team_roles = load_team_tree_permissions(self).team_roles
        return [team_id for team_id, role in team_roles.items() if role]

    @property
    def listable_team_ids(self):
        """All teams user can see (excluding departments)"""
        result = load_team_tree_permissions(self)
        return get_team_ids_from_team_tree(result, self)

    @property
    def listable_department_ids(self):
        """All departments user can see"""
        result = load_team_tree_permissions(self)
        return get_department_ids_from_team_tree(result)

    def get_listable_department_team_ids(self, department_id):
        """All teams user can see in selected department"""
        result = load_team_tree_permissions(self)
        return get_department_team_ids_from_team_tree(result, self, department_id)

    @property
    def writable_teams(self):
        if self.is_superadmin:
            return Team.query

        return Team.query.filter(Team.team_id.in_(self.writable_team_ids))

    @property
    def writable_team_ids(self):
        if self.is_superadmin:
            return [team_id for team_id, in Team.query.with_entities(Team.team_id)]

        team_roles = load_team_tree_permissions(self).team_roles
        return [
            team_id
            for team_id, role in team_roles.items()
            if role == TeamRoleEnum.team_admin.value
        ]


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


def find_role_from_parents(team_roles, team_parents, team_id):
    """Searches for the first parent with defined role

    >>> find_role_from_parents({42: 'member'}, {1: 2, 2: 42}, 1)
    'member'
    """
    if team_roles.get(team_id) is not None:
        return team_roles[team_id]

    current_team_id = team_id
    visited = []

    while True:
        visited.append(current_team_id)

        current_team_id = team_parents.get(current_team_id)
        if current_team_id is None:
            return None  # at the top of the tree

        if current_team_id in visited:
            raise ValueError(
                "Cycles in the tree; path: {} -> {}".format(visited, current_team_id)
            )

        current_team_role = team_roles.get(current_team_id)

        if current_team_role is not None:
            return current_team_role


TeamTreeResult = namedtuple(
    "TeamTreeResult", ["team_roles", "team_parents", "team_children"],
)


def load_team_tree_permissions(user: User) -> TeamTreeResult:

    if user.is_superadmin:
        result = db.session.execute(
            text("""SELECT team_id, parent_id, NULL FROM teams;""")
        )
    else:
        # for each team we have defined access, load all parents and all children
        # parents are needed for department picker (included even if no access to dep)
        # children are needed if access is given on department level
        result = db.session.execute(
            text(
                """
                WITH RECURSIVE team_tree AS (
                    SELECT t.team_id, t.parent_id, ut.role
                        FROM user_team AS ut, teams AS t
                        WHERE t.team_id = ut.team_id AND ut.user_id = :user_id
                    UNION
                        SELECT x.team_id, x.parent_id, b.role
                        FROM team_tree tt, teams x
                        LEFT JOIN user_team AS b ON (
                            b.team_id = x.team_id
                            AND b.user_id = :user_id
                        )
                        WHERE x.team_id = tt.parent_id OR tt.team_id = x.parent_id
                ) SELECT * FROM team_tree;"""
            ),
            {"user_id": user.id},
        )

    team_roles = {}  # team id -> role/None
    team_parents = {}  # team id -> parent team id
    team_children = defaultdict(set)  # team id -> children

    for team_id, parent_id, role in result:
        team_roles[team_id] = role
        if parent_id:
            team_parents[team_id] = parent_id
            team_children[parent_id].add(team_id)

    for team_id, role in team_roles.items():
        if role is not None:
            continue
        team_roles[team_id] = find_role_from_parents(team_roles, team_parents, team_id)

    return TeamTreeResult(team_roles, team_parents, team_children)


def get_department_ids_from_team_tree(result: TeamTreeResult):
    # all teams with children
    return list(result.team_children)


def get_team_ids_from_team_tree(result: TeamTreeResult, user: User):
    # all teams without children, user has access to

    team_roles = result.team_roles
    team_children = result.team_children

    is_superadmin = user.is_superadmin

    return [
        team_id
        for team_id, role in team_roles.items()
        if (
            team_id not in team_children
            and (is_superadmin or role is not None)  # excluding teams without access
        )
    ]


def get_department_team_ids_from_team_tree(
    result: TeamTreeResult, user: User, department_id: int
):
    # all department's subteams without children, user has access to

    team_roles = result.team_roles
    team_children = result.team_children

    is_superadmin = user.is_superadmin

    selected_department_team_ids = []

    check_has_children = list(team_children[department_id])
    while check_has_children:
        checking_team_id = check_has_children.pop()

        if checking_team_id in team_children:
            check_has_children.extend(team_children[checking_team_id])
        elif is_superadmin or team_roles.get(checking_team_id) is not None:
            selected_department_team_ids.append(checking_team_id)

    return selected_department_team_ids
