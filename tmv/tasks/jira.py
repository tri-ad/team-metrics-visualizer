import traceback
from datetime import datetime, timedelta

from celery.schedules import crontab  # pylint: disable=unused-import
from dateutil.tz import tzutc

from connectors.jira.jira_sync import JiraSync
from database import db  # pylint: disable=unused-import
from runcelery import celery as celery_app
from structure.events import Sprint
from structure.project import JiraProject, Activity


@celery_app.task()
def sync_assigned_projects():
    jira_projects = JiraProject.query.filter(JiraProject.activity != None).all()
    jira_sync = JiraSync()
    for project in jira_projects:
        jira_sync.snapshot_project(project)
    # TODO: other types of projects
    return True


@celery_app.task()
def sync_sprint_issues(sprint_id, latest_only):
    jira_sprint = Sprint.query.filter(
        Sprint.sprint_id == sprint_id, Sprint.jira_sprint_id != None
    ).one_or_none()
    if jira_sprint:
        jira_sync = JiraSync()
        jira_sync.sync_sprint_issues(jira_sprint, latest_only)
    # TODO: other types of sprints
    return True


@celery_app.task(bind=True)
def sync_activity_past_data(self, activity_id, days=90):
    from flask import current_app  # pylint: disable=import-outside-toplevel

    time_now = datetime.now(tzutc())
    jira_sprints = Sprint.query.filter(
        Sprint.jira_sprint_id != None,
        Sprint.activity_id == activity_id,
        Sprint.start_date >= time_now - timedelta(days=days),
    ).all()
    if jira_sprints:
        jira_sync = JiraSync()
        for idx, sprint in enumerate(jira_sprints):
            message = f"Syncing sprint {sprint.name}"
            current_app.logger.info(message)
            jira_sync.sync_sprint_issues(sprint, False)
            self.update_state(
                state="PROGRESS",
                meta={"current": idx, "total": len(jira_sprints), "status": message},
            )
        return {
            "current": len(jira_sprints),
            "total": len(jira_sprints),
            "status": "Complete",
        }
    else:
        # TODO: other types of sprints
        return {"current": 1, "total": 1, "status": "No sprints found"}


@celery_app.task()
def sync_all_sprints_without_issues(activity_id):
    from flask import current_app  # pylint: disable=import-outside-toplevel

    try:
        activity = Activity.query.get(activity_id)
        jira_project = JiraProject.query.filter(
            JiraProject.activity == activity
        ).one_or_none()
        if jira_project:
            jira_sync = JiraSync()
            jira_sync.sync_all_sprints(jira_project)
        # TODO: other types of projects
        return True
    except Exception:
        current_app.logger.error(traceback.format_exc())
        current_app.logger.error("Failed to sync sprints")
        return False
