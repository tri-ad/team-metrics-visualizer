# pylint: disable=unnecessary-lambda

import pytest
from dataclasses import dataclass
from datetime import datetime
from dateutil.parser import isoparse
from dateutil.tz import tzutc
from unittest.mock import Mock, patch

from database import db
from structure.events import IssueSnapshot, Sprint
from structure.organization import Team
from structure.project import Activity, JiraProject
from connectors.jira.jira_sync import JiraSync


@dataclass
class StatusCategory:
    name: str


@dataclass
class Status:
    name: str
    statusCategory: StatusCategory


@dataclass
class Issue:
    raw: dict


JIRA_FIELDS = [
    {
        "id": "customfield_10020",
        "key": "customfield_10020",
        "name": "Sprint",
        "custom": True,
        "orderable": True,
        "navigable": True,
        "searchable": True,
        "clauseNames": ["cf[10020]", "Sprint"],
        "schema": {
            "type": "array",
            "items": "string",
            "custom": "com.pyxis.greenhopper.jira:gh-sprint",
            "customId": 10020,
        },
    },
    {
        "id": "customfield_10024",
        "key": "customfield_10024",
        "name": "Story Points",
        "custom": True,
        "orderable": True,
        "navigable": True,
        "searchable": True,
        "clauseNames": ["cf[10024]", "Story Points"],
        "schema": {
            "type": "number",
            "custom": "com.atlassian.jira.plugin.system.customfieldtypes:float",
            "customId": 10024,
        },
    },
]
JIRA_STATUSES = [
    Status("In Progress", StatusCategory("In Progress")),
    Status("To Do", StatusCategory("To Do")),
    Status("Done", StatusCategory("Done")),
]
SPRINT_START_DATE = "2020-04-09T08:02:27.921Z"
SPRINT_END_DATE = "2020-04-23T08:22:27.921Z"


def search_issues(*args, **kwargs):
    issues_list = []
    if "In Progress" in args[0]:
        status_range = range(0, 5)
    elif "To Do" in args[0]:
        status_range = range(5, 10)
    elif "Done" in args[0]:
        status_range = range(10, 15)
    else:
        # status wasn't queried in the jql
        status_range = range(15)

    for i in status_range:
        issues_list.append(
            Issue(
                {
                    "expand": "operations,versionedRepresentations,editmeta,changelog,renderedFields",
                    "id": f"{i}",
                    "self": "https://sample-jira.atlassian.net/rest/api/2/issue/10038",
                    "key": f"SSP-{i}",
                    "versionedRepresentations": {
                        "customfield_10020": {
                            "1": [
                                f"com.atlassian.greenhopper.service.sprint.Sprint@62cc8423[id=7,rapidViewId=<null>,state=ACTIVE,name=Sample Sprint 2,='\",goal=we can use B&W, test case tool works,  code is refactored and c++ and python works,startDate={SPRINT_START_DATE},endDate={SPRINT_END_DATE},completeDate=<null>,sequence=7]"
                            ],
                            "2": [
                                {
                                    "id": 7,
                                    "name": "Sample Sprint 2",
                                    "state": "active",
                                    "startDate": SPRINT_START_DATE,
                                    "endDate": SPRINT_END_DATE,
                                }
                            ],
                        },
                        "status": {
                            "1": {
                                "self": "https://sample-jira.atlassian.net/rest/api/2/status/10001",
                                "description": "",
                                "iconUrl": "https://sample-jira.atlassian.net/",
                                "name": "Done",
                                "id": "10001",
                                "statusCategory": {
                                    "self": "https://sample-jira.atlassian.net/rest/api/2/statuscategory/3",
                                    "id": 3,
                                    "key": "done",
                                    "colorName": "green",
                                    "name": "Done",
                                },
                            }
                        },
                    },
                }
            )
        )
    return issues_list


def search_issues_inc_sprint_dict(*args, **kwargs):
    issues_list = []
    if "In Progress" in args[0]:
        status_range = range(0, 5)
    elif "To Do" in args[0]:
        status_range = range(5, 10)
    elif "Done" in args[0]:
        status_range = range(10, 15)
    else:
        # status wasn't queried in the jql
        status_range = range(15)

    for i in status_range:
        issues_list.append(
            Issue(
                {
                    "expand": "operations,versionedRepresentations,editmeta,changelog,renderedFields",
                    "id": f"{i}",
                    "self": "https://sample-jira.atlassian.net/rest/api/2/issue/10038",
                    "key": f"SSP-{i}",
                    "versionedRepresentations": {
                        "customfield_10020": {
                            "1": [
                                f"com.atlassian.greenhopper.service.sprint.Sprint@62cc8423[id=7,rapidViewId=<null>,state=ACTIVE,name=Sample Sprint 2,goal=<null>,startDate={SPRINT_START_DATE},endDate={SPRINT_END_DATE},completeDate=<null>,sequence=7]"
                            ],
                            "2": [
                                {"id": 7, "name": "Sample Sprint 2", "state": "active",}
                            ],
                        },
                        "status": {
                            "1": {
                                "self": "https://sample-jira.atlassian.net/rest/api/2/status/10001",
                                "description": "",
                                "iconUrl": "https://sample-jira.atlassian.net/",
                                "name": "Done",
                                "id": "10001",
                                "statusCategory": {
                                    "self": "https://sample-jira.atlassian.net/rest/api/2/statuscategory/3",
                                    "id": 3,
                                    "key": "done",
                                    "colorName": "green",
                                    "name": "Done",
                                },
                            }
                        },
                    },
                }
            )
        )
    return issues_list


@pytest.mark.usefixtures("app")
class TestJiraSync:
    def setup_required_objects(self):
        team = Team(parent_team=None, code="ABC", name="Team ABC")
        db.session.add(team)

        project = JiraProject(project_key="TP-1", project_name="Test Project 1")
        db.session.add(project)
        db.session.commit()

        activity = Activity(
            team_id=team.team_id,
            activity_name="ABC Activity",
            jira_project_id=project.id,
        )
        db.session.add(activity)
        db.session.commit()

    @patch("connectors.jira.jira_sync.jira_core")
    @patch("connectors.jira.jira_sync.datetime")
    def test_sync_project_in_sprint(self, mock_datetime, mock_jira_core):
        self.setup_required_objects()

        # mock datetime within sprint duration
        mock_datetime.now.return_value = datetime(2020, 4, 15, 23, 59, tzinfo=tzutc())
        mock_datetime.side_effect = lambda *args, **kw: datetime(*args, **kw)

        # mock jira calls
        mock_jira = Mock()
        mock_jira.fields.return_value = JIRA_FIELDS
        mock_jira.statuses.return_value = JIRA_STATUSES
        mock_jira.search_issues.side_effect = search_issues
        mock_jira_core.connect.return_value = mock_jira

        j = JiraSync()
        j.snapshot_project(JiraProject.query.first())
        issues = IssueSnapshot.query.all()

        assert len(issues) == 15

        for issue in issues:
            assert issue.sprint is not None

    @patch("connectors.jira.jira_sync.jira_core")
    @patch("connectors.jira.jira_sync.datetime")
    def test_sync_project_in_sprint_inc_jira_data(self, mock_datetime, mock_jira_core):
        """
        Tests for if jira's json representation of sprint is incomplete
        """
        self.setup_required_objects()

        # mock datetime within sprint duration
        mock_datetime.now.return_value = datetime(2020, 4, 15, 23, 59, tzinfo=tzutc())
        mock_datetime.side_effect = lambda *args, **kw: datetime(*args, **kw)

        # mock jira calls
        mock_jira = Mock()
        mock_jira.fields.return_value = JIRA_FIELDS
        mock_jira.statuses.return_value = JIRA_STATUSES
        mock_jira.search_issues.side_effect = search_issues_inc_sprint_dict
        mock_jira_core.connect.return_value = mock_jira

        j = JiraSync()
        j.snapshot_project(JiraProject.query.first())
        issues = IssueSnapshot.query.all()

        assert len(issues) == 15

        for issue in issues:
            assert issue.sprint is not None

    @patch("connectors.jira.jira_sync.jira_core")
    @patch("connectors.jira.jira_sync.datetime")
    def test_sync_project_outside_sprint(self, mock_datetime, mock_jira_core):
        self.setup_required_objects()

        # mock datetime not within sprint duration
        mock_datetime.now.return_value = datetime(2020, 5, 15, 23, 59, tzinfo=tzutc())
        mock_datetime.side_effect = lambda *args, **kw: datetime(*args, **kw)

        # mock jira calls
        mock_jira = Mock()
        mock_jira.fields.return_value = JIRA_FIELDS
        mock_jira.statuses.return_value = JIRA_STATUSES
        mock_jira.search_issues.side_effect = search_issues
        mock_jira_core.connect.return_value = mock_jira

        j = JiraSync()
        j.snapshot_project(JiraProject.query.first())
        issues = IssueSnapshot.query.all()

        assert len(issues) == 0

    @patch("connectors.jira.jira_sync.jira_core")
    def test_sync_sprints(self, mock_jira_core):
        self.setup_required_objects()

        # mock jira calls
        mock_jira = Mock()
        mock_jira.fields.return_value = JIRA_FIELDS
        mock_jira.statuses.return_value = JIRA_STATUSES
        mock_jira.search_issues.side_effect = search_issues
        mock_jira_core.connect.return_value = mock_jira

        sprints = Sprint.query.all()
        assert len(sprints) == 0

        j = JiraSync()
        j.sync_all_sprints(JiraProject.query.first())
        sprints = Sprint.query.all()

        assert len(sprints) == 1

    @patch("connectors.jira.jira_sync.jira_core")
    def test_sync_sprint_issues(self, mock_jira_core):
        self.setup_required_objects()

        # mock jira calls
        mock_jira = Mock()
        mock_jira.fields.return_value = JIRA_FIELDS
        mock_jira.statuses.return_value = JIRA_STATUSES
        mock_jira.search_issues.side_effect = search_issues
        mock_jira_core.connect.return_value = mock_jira

        j = JiraSync()
        j.sync_all_sprints(JiraProject.query.first())
        j.sync_sprint_issues(Sprint.query.first())
        sprint = Sprint.query.first()
        issue_snapshots = sprint.issue_snapshots

        start_date = isoparse(SPRINT_START_DATE)
        end_date = isoparse(SPRINT_END_DATE)
        timedelta_days = (end_date - start_date).days

        # add 1 to timedelta because query is inclusive
        assert len(issue_snapshots) == (timedelta_days + 1) * 15
