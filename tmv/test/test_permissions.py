import pytest
from database import db
from structure.organization import Team
from structure.auth import (
    User,
    UserTeam,
    find_role_from_parents,
    load_team_tree_permissions,
    TeamRoleEnum,
    get_department_ids_from_team_tree,
    get_team_ids_from_team_tree,
    get_department_team_ids_from_team_tree,
)


def create_setup(data):
    u = User(email="test@localhost")
    db.session.add(u)
    db.session.flush()

    team_id_by_name = {}

    def _create_teams(l, parent_id=None):
        for team_name, role, children in l:
            t = Team(name=team_name, code=team_name, parent_id=parent_id)
            db.session.add(t)
            db.session.flush()
            if role:
                ut = UserTeam(user=u, team=t, role=role)
                db.session.add(ut)
            db.session.flush()

            team_id_by_name[team_name] = t.team_id

            _create_teams(children, parent_id=t.team_id)

    _create_teams(data)

    db.session.commit()
    return u, team_id_by_name


@pytest.mark.usefixtures("app")
class TestPermissions:
    def test_find_role_from_parents(self):
        role = find_role_from_parents({42: "member"}, {1: 2, 2: 42}, 1)
        assert role == "member"

    def test_find_role_from_parents_1(self):
        role = find_role_from_parents({42: "member", 2: "team_admin"}, {1: 2, 2: 42}, 1)
        assert role == "team_admin"

    def test_find_role_from_parents_cycle(self):
        with pytest.raises(ValueError):
            find_role_from_parents({1: None, 2: None}, {1: 2, 2: 1}, 1)

    def test_load_team_tree_permissions_no_access(self):
        u = User(email="test@localhost")
        db.session.add(u)
        db.session.add(Team(name="A", code="A"))
        db.session.commit()

        result = load_team_tree_permissions(u)
        assert len(result.team_roles) == 0
        assert len(result.team_parents) == 0
        assert len(result.team_children) == 0

    def test_load_team_tree_permissions(self):
        # fmt: off
        u, t = create_setup([
            ('dep1', None, [
                ('dep2', None, [
                    ('dep2_team1', TeamRoleEnum.member.value, []),
                ])
            ]),
        ])
        # fmt: on
        result = load_team_tree_permissions(u)

        assert result.team_roles == {
            t["dep1"]: None,
            t["dep2"]: None,
            t["dep2_team1"]: TeamRoleEnum.member.value,
        }
        assert result.team_parents == {
            t["dep2_team1"]: t["dep2"],
            t["dep2"]: t["dep1"],
        }
        assert result.team_children == {
            t["dep1"]: {t["dep2"]},
            t["dep2"]: {t["dep2_team1"]},
        }

    def test_load_team_tree_permissions_department(self):
        # fmt: off
        u, t = create_setup([
            ('dep1', None, [
                ('dep2', TeamRoleEnum.member.value, [
                    ('dep2_team1', None, []),
                    ('dep2_team2', None, []),
                ])
            ])
        ])
        # fmt: on
        result = load_team_tree_permissions(u)
        assert result.team_roles == {
            t["dep1"]: None,
            t["dep2"]: TeamRoleEnum.member.value,
            t["dep2_team1"]: TeamRoleEnum.member.value,
            t["dep2_team2"]: TeamRoleEnum.member.value,
        }

        self._assert_test_load_team_tree_permissions_department(u, t, result)

    def _assert_test_load_team_tree_permissions_department(self, u, t, result):
        assert set(u.readable_team_ids) == set(
            [t["dep2"], t["dep2_team1"], t["dep2_team2"]]
        )

        assert set(get_department_ids_from_team_tree(result)) == set(
            [t["dep1"], t["dep2"]]
        )
        assert set(u.listable_department_ids) == set([t["dep1"], t["dep2"]])

        assert set(get_team_ids_from_team_tree(result, u)) == set(
            [t["dep2_team1"], t["dep2_team2"],]
        )
        assert set(u.listable_team_ids) == set([t["dep2_team1"], t["dep2_team2"]])

        assert set(get_department_team_ids_from_team_tree(result, u, t["dep1"])) == set(
            [t["dep2_team1"], t["dep2_team2"]]
        )
        assert set(get_department_team_ids_from_team_tree(result, u, t["dep2"])) == set(
            [t["dep2_team1"], t["dep2_team2"]]
        )

    def test_load_team_tree_permissions_department_1(self):
        # fmt: off
        u, t = create_setup([
            ('dep1', None, [
                ('dep2', TeamRoleEnum.member.value, [
                    ('dep2_team1', None, []),
                    ('dep2_team2', None, []),
                ]),
                ('dep1_team1', None, []),
            ]),
            ('dep3', None, [
                ('dep3_team1', None, []),
                ('dep4', None, [
                    ('dep4_team1', None, []),
                ]),
            ]),
            ('team1', None, []),
        ])
        # fmt: on
        result = load_team_tree_permissions(u)

        assert result.team_roles == {
            t["dep1"]: None,
            t["dep1_team1"]: None,
            t["dep2"]: TeamRoleEnum.member.value,
            t["dep2_team1"]: TeamRoleEnum.member.value,
            t["dep2_team2"]: TeamRoleEnum.member.value,
        }
        # dep3.* and team1 should be ignored, so same asserts as in
        # `test_load_team_tree_permissions_department`
        self._assert_test_load_team_tree_permissions_department(u, t, result)

    def test_load_team_tree_permissions_department_deep(self):
        # fmt: off
        u, t = create_setup([
            ('dep1', TeamRoleEnum.member.value, [
                ('dep2', None, [
                    ('dep2_team1', None, []),
                    ('dep2_team2', None, []),
                ])
            ])
        ])
        # fmt: on
        result = load_team_tree_permissions(u)
        assert result.team_roles == {
            t["dep1"]: TeamRoleEnum.member.value,
            t["dep2"]: TeamRoleEnum.member.value,
            t["dep2_team1"]: TeamRoleEnum.member.value,
            t["dep2_team2"]: TeamRoleEnum.member.value,
        }

    def test_load_team_tree_permissions_override(self):
        # fmt: off
        u, t = create_setup([
            ('dep1', None, [
                ('dep2', TeamRoleEnum.team_admin.value, [
                    ('dep2_team1', None, []),
                    ('dep2_team2', TeamRoleEnum.member.value, []),
                ])
            ]),
            ('dep3', None, []),
        ])
        # fmt: on
        result = load_team_tree_permissions(u)

        assert result.team_roles == {
            t["dep1"]: None,
            t["dep2"]: TeamRoleEnum.team_admin.value,
            t["dep2_team1"]: TeamRoleEnum.team_admin.value,
            t["dep2_team2"]: TeamRoleEnum.member.value,  # !
        }
        assert set(u.readable_team_ids) == set(
            [t["dep2"], t["dep2_team1"], t["dep2_team2"]]
        )
        assert set(u.writable_team_ids) == set([t["dep2"], t["dep2_team1"]])
