import logging
import re
from datetime import date, datetime, timedelta
from typing import Dict, List, Optional, Tuple

from dateutil import rrule
from dateutil.parser import isoparse
from dateutil.tz import tzutc
from dateutil.utils import default_tzinfo
from flask import current_app
from sqlalchemy.dialects.postgresql import insert as pg_insert

from common.exceptions import ImproperlyConfiguredError
from connectors.jira import jira_core
from database import db
from structure.events import IssueSnapshot, Sprint
from structure.project import JiraProject


class JiraSync:
    def __init__(self):
        """
        Stores all the issue statuses and issue fields from jira.
        """
        self.jira = jira_core.connect()
        self.status_mapping = {
            d.name: d.statusCategory.name for d in self.jira.statuses()
        }
        self.statuses = self.status_mapping.keys()
        self.issue_fields_mapping = {f["name"]: f["id"] for f in self.jira.fields()}

        self.sprint_field = self._get_field_key(current_app.config["JIRA_FIELD_SPRINT"])
        self.storypoints_field = self._get_field_key(
            current_app.config["JIRA_FIELD_STORYPOINTS"]
        )

    def _get_field_key(self, name: str) -> str:
        """
        Returns the mapping of name to the jira field this class needs
        or raises error.

        :param name: Name of the case-sensitive jira field (e.g., Sprint)
        :type name: str
        """
        try:
            return self.issue_fields_mapping[name]
        except KeyError:
            logging.error(
                f"JIRA field name `{name}` does not exist. "
                f"Update your `JIRA_FIELD_*` env vars. "
                f"Available values: `{'`, `'.join(self.issue_fields_mapping.keys())}`"
            )
            raise ImproperlyConfiguredError(
                f"Unable to find JIRA field mapping for `{name}`"
            )

    def _get_fields(self, extra: Optional[List[str]] = None) -> List[str]:
        """
        Returns the names of the fields we need in the jql.

        :param extra: list of field names to include in the query.
        """
        fields = [
            "status",
            "id",
            "key",
            self.sprint_field,
            self.storypoints_field,
        ]
        if extra:
            fields.append(extra)
        return fields

    def _get_issues_by_project(
        self, project_key: str, dt: Optional[datetime] = None,
    ):
        """
        Queries JIRA and returns issues under project_key
        that have any status on the given date.

        :param project_key: String to determine the project to query.
        :param dt: Datetime to filter issues.
        """
        jql_base = f"""project="{project_key}" """
        issues_list = []
        if dt:
            snapshot_dt = dt.strftime(
                "%Y-%m-%d %H:%M"
            )  # Note: jql doesn't support timezones
            for status in self.statuses:
                jql = (
                    jql_base + f"""AND status WAS "{status}" """
                    f"""ON "{snapshot_dt}" """
                )
                issues = self.jira.search_issues(
                    jql,
                    expand="versionedRepresentations",
                    fields=self._get_fields(),
                    maxResults=False,
                )
                # need to add this for parsing later
                for issue in issues:
                    issue.raw["status"] = status
                issues_list += issues
        else:
            issues_list = self.jira.search_issues(
                jql_base,
                expand="versionedRepresentations",
                fields=self._get_fields(),
                maxResults=False,
            )
        return issues_list

    def _get_issues_by_sprint(self, sprint: Sprint, latest_only: bool = False) -> dict:
        """
        Queries JIRA and returns issues under sprint

        :param sprint: Sprint object to query
        :param latest_only: Gets issues for latest date only if True
        """
        # future sprints won't have issues
        if sprint.is_future:
            return {}
        jql_base = f"""sprint = {sprint.jira_sprint_id} """

        time_now = datetime.now(tzutc())
        # if latest_only, get just today's data
        if latest_only:
            issues = self.jira.search_issues(
                jql_base,
                expand="versionedRepresentations",
                fields=self._get_fields(),
                maxResults=False,
            )
            return {time_now: issues}

        # get data for all dates
        until_date = sprint.complete_date or sprint.end_date
        time_now = time_now.replace(tzinfo=None)
        if until_date > time_now:
            until_date = time_now
        # inclusive count
        sprint_days_cnt = (until_date.date() - sprint.start_date.date()).days + 1
        index = list(
            rrule.rrule(
                rrule.DAILY,
                dtstart=sprint.start_date.date(),
                count=sprint_days_cnt,
                byhour=23,
                byminute=59,
                bysecond=59,
            )
        )
        # this means sprint is current so last entry shouldn't be EOD
        if until_date == time_now:
            index = index[:-1] + [until_date]
        issues_per_day = {k: [] for k in index}

        for dt in index:
            snapshot_dt = dt.strftime(
                "%Y-%m-%d %H:%M"
            )  # Note: jql doesn't support timezones
            for status in self.statuses:
                jql = (
                    jql_base + f"""AND status WAS "{status}" """
                    f"""ON "{snapshot_dt}" """
                )
                issues = self.jira.search_issues(
                    jql,
                    expand="versionedRepresentations",
                    fields=self._get_fields(),
                    maxResults=False,
                )
                # need to add this for parsing later
                for issue in issues:
                    issue.raw["status"] = status
                issues_per_day[dt] += issues
        return issues_per_day

    def _gh_string_to_dict(self, gh_string: str) -> dict:
        """
        Converts a greenhopper string to dict

        :param gh_string: string of the form:
            "com.atlassian.greenhopper.service.sprint.Sprint@4b4ba6e9[id=10,rapidViewId=2,state=FUTURE,name=Sample Sprint 2,goal=<null>,startDate=<null>,endDate=<null>,completeDate=<null>,sequence=10]"
        """
        return_dict = {}
        if gh_string.startswith("com.atlassian.greenhopper.service.sprint.Sprint"):
            _, kv_list_str = gh_string.split("[", maxsplit=1)
            kv_list_str = gh_string[gh_string.index("[") : -1]
            # match key=value if text afterwards is ",key="
            tokens_list = re.findall(r"(\w+=.*?)(?=,\w+=)", kv_list_str + ",a=")
            return_dict = dict(kv.split("=", maxsplit=1) for kv in tokens_list)
            for k, v in return_dict.items():
                if v == "<null>":
                    return_dict[k] = None
        else:
            current_app.logger.error(f"Unsupported greenhopper object: {gh_string}")
        return return_dict

    def _get_relevant_sprint(
        self, sprint_field_value: Dict, dt: datetime
    ) -> Tuple[Optional[str], Optional[Dict]]:
        """
        Given a list of sprints, returns the one that's active during
        given date.

        Note: As returned from the jira api, sprints are ordered by date.

        :param sprint_list: A dict of list of sprints as returned by the JIRA api.
            By default, these are ordered by date.
        :param dt: Used to determine the sprint most relevant to this datetime.
        """
        if not sprint_field_value["1"] and not sprint_field_value["2"]:
            return None, None

        sprint_list = zip(sprint_field_value["1"], sprint_field_value["2"])

        for sprint_gh, sprint_dict in sprint_list:
            try:
                sprint_state = Sprint.State(sprint_dict["state"].lower())
            except ValueError as e:
                logger.error(
                    f"Encountered Sprint with invalid state: {e}. Context: {sprint_dict}"
                )
            else:
                if sprint_state == Sprint.State.FUTURE:
                    return sprint_gh, sprint_dict
                sprint_gh_dict = self._gh_string_to_dict(sprint_gh)
                start_date = isoparse(
                    sprint_dict.get("startDate") or sprint_gh_dict.get("startDate")
                ).astimezone(tzutc())
                end_date = isoparse(
                    sprint_dict.get("endDate") or sprint_gh_dict.get("endDate")
                ).astimezone(tzutc())
                if sprint_dict.get("completeDate"):
                    end_date = isoparse(sprint_dict["completeDate"]).astimezone(tzutc())
                elif sprint_gh_dict.get("completeDate"):
                    end_date = isoparse(sprint_gh_dict["completeDate"]).astimezone(
                        tzutc()
                    )
                if start_date <= dt <= end_date:
                    return sprint_gh, sprint_dict
        return None, None

    def _create_or_update_sprint(
        self,
        sprint_tuple: Tuple[str, Dict],
        activity_id: int,
        dt: datetime,
        return_obj: bool = False,
        set_last_updated: bool = True,
    ):
        """
        Create or update a sprint based on datetime dt

        :param sprint_tuple: tuple of the same sprint represented
            as a greenhopper object and a json object.
        :param activity_id: activity id to tie the sprint to
        :param dt: datetime to check for last_updated field
        :param return_obj: boolean if a sprint object is needed
        :param set_last_updated: boolean if last_updated is to be set.
            Set this to False if you're not updating IssueSnapshots.
        """
        sprint_gh, sprint_dict = sprint_tuple
        sprint = Sprint.query.filter_by(jira_sprint_id=sprint_dict["id"]).one_or_none()

        # create sprint if it doesn't exist. update if last_updated < dt
        if not sprint or not sprint.last_updated or sprint.tz_last_updated < dt:
            try:
                sprint_state = Sprint.State(sprint_dict["state"].lower())
            except ValueError as e:
                logger.error(f"Encountered Sprint with invalid state: {e}")
                return None
            else:
                sprint_gh_dict = self._gh_string_to_dict(sprint_gh)
                params = {
                    "activity_id": activity_id,
                    "jira_sprint_id": sprint_dict["id"],
                    "name": sprint_dict["name"],
                    "state": sprint_state.value,
                    "start_date": sprint_dict.get("startDate")
                    or sprint_gh_dict.get("startDate"),
                    "end_date": sprint_dict.get("endDate")
                    or sprint_gh_dict.get("endDate"),
                    "complete_date": sprint_dict.get("completeDate")
                    or sprint_gh_dict.get("completeDate"),
                }
            if set_last_updated:
                params["last_updated"] = datetime.now(tzutc())
            stmt = (
                pg_insert(Sprint)
                .values(**params)
                .on_conflict_do_update(
                    constraint="uq_sprints_jira_sprint_id",
                    set_={k: v for k, v in params.items() if k != "jira_sprint_id"},
                )
            )
            db.session.execute(stmt)
            db.session.commit()
            if not sprint and return_obj:
                sprint = Sprint.query.filter_by(
                    jira_sprint_id=params["jira_sprint_id"]
                ).one_or_none()

        if return_obj:
            return sprint

    def _parse_issue(
        self,
        issue_raw: dict,
        dt: datetime = None,
        activity_id: int = None,
        sprint: Sprint = None,
    ) -> dict:
        """
        Given the dict representation of issue from JIRA:
        - creates the Sprint as needed (if not provided)
        - returns the formatted fields for IssueSnapshot

        :param issue_raw: Raw dict representation of issue
        :param dt: Datetime to put issue into context if sprint not provided.
            This is mainly used to retrieve the sprint relevant to the issue.
        :param activity_id: Activity id for Sprint creation use if sprint
            not needed.
        :param sprint: Sprint so that creation no longer needed.
        """
        if not sprint:
            if activity_id is None and dt is None:
                raise Exception("activity_id and dt needed if sprint not provided.")

            sprint_tuple = self._get_relevant_sprint(
                issue_raw["versionedRepresentations"][self.sprint_field], dt
            )
            if sprint_tuple[0]:
                sprint = self._create_or_update_sprint(
                    sprint_tuple, activity_id, dt, return_obj=True
                )

        if "status" in issue_raw:
            # manually-set status for past issues
            status = issue_raw["status"]
        else:
            # present status as returned by JIRA API
            status = issue_raw["versionedRepresentations"]["status"]["1"]["name"]

        clean_data = {
            "issue_id": issue_raw["id"],
            "status": status,
            "sprint_id": sprint.sprint_id if sprint else None,
        }
        story_points = issue_raw["versionedRepresentations"].get(self.storypoints_field)
        if story_points and story_points.get("1") is not None:
            clean_data["story_points"] = story_points["1"]
        else:
            clean_data["story_points"] = 0

        return clean_data

    def snapshot_project(self, project: JiraProject):
        """
        Takes a current snapshot of all issues of a project. It does so
        by creating IssueSnapshot objects that store story points and status.
        In the process, it also creates Sprint objects if necessary.

        :param project: JiraProject object to tie the issues queried to.
            The jql needs the `project_key` field of `project`.
        """
        activity_id = project.activity.activity_id
        issues = self._get_issues_by_project(project.project_key)

        # for date stamping
        dt = datetime.now(tzutc())

        for issue in issues:
            parsed_issue = self._parse_issue(issue.raw, dt=dt, activity_id=activity_id)
            # skip if there's no sprint
            if parsed_issue["sprint_id"]:
                issue_obj = IssueSnapshot(snapshot_date=dt, **parsed_issue,)
                db.session.add(issue_obj)
        try:
            db.session.commit()
        except:
            logging.error(
                f"Error encountered in syncing issues. project_id={project.id}, dt={dt}"
            )
            db.session.rollback()

    def sync_sprint_issues(self, sprint: Sprint, latest_only: bool = False):
        """
        Gets and syncs all issues in sprint

        :param sprint: Sprint object to limit date
        :param latest_only: If True, syncs only latest data from jira (today).
            By default (False), syncs all dates.
        """
        time_now = datetime.now(tzutc())
        issues_per_day = self._get_issues_by_sprint(
            sprint, time_now if latest_only else None
        )
        for date_key, issues_list in issues_per_day.items():
            for issue in issues_list:
                parsed_issue = self._parse_issue(issue.raw, sprint=sprint)
                issue_obj = IssueSnapshot(snapshot_date=date_key, **parsed_issue,)
                db.session.add(issue_obj)

        sprint.last_updated = time_now
        try:
            db.session.commit()
        except:
            logging.error(
                f"Error encountered in syncing issues. sprint_id={sprint.sprint_id}"
            )
            db.session.rollback()

    def sync_all_sprints(self, project: JiraProject):
        """
        Gets and syncs all the sprints but without the issues.

        :param project: JiraProject object to query sprints
        """
        time_now = datetime.now(tzutc())
        activity_id = project.activity.activity_id

        issues = self._get_issues_by_project(project.project_key)

        collated_sprints = dict()
        for issue in issues:
            sprint_field_value = issue.raw["versionedRepresentations"][
                self.sprint_field
            ]
            if sprint_field_value["1"] and sprint_field_value["2"]:
                sprint_list = zip(sprint_field_value["1"], sprint_field_value["2"])

                # collate sprints to save on db calls
                for sprint_gh, sprint_dict in sprint_list:
                    collated_sprints[sprint_dict["id"]] = (sprint_gh, sprint_dict)

        for _, sprint_tuple in collated_sprints.items():
            self._create_or_update_sprint(
                sprint_tuple, activity_id, time_now, set_last_updated=False
            )
