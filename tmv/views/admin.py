import logging
import traceback
from datetime import datetime, timedelta
from typing import Optional

from dateutil.tz import tzutc
from flask import (
    Blueprint,
    current_app,
    flash,
    Flask,
    jsonify,
    redirect,
    request,
    session,
    url_for,
)
from flask_admin import Admin, BaseView, expose, AdminIndexView
from flask_admin.contrib.sqla.fields import QuerySelectField
from flask_admin.helpers import get_form_data, get_redirect_target
from flask_admin.model.form import InlineFormAdmin
from flask_admin.model.helpers import get_mdict_item_or_list
from flask_admin.menu import MenuLink
from flask_admin.form.fields import Select2Field, DateTimeField
from flask_admin.contrib.sqla import ModelView
from flask_security import current_user, login_required
from flask_security.utils import encrypt_password
from sqlalchemy import func
from sqlalchemy.dialects.postgresql import insert as pg_insert
from wtforms import form
from wtforms.fields import PasswordField, HiddenField, SelectField, StringField
from wtforms.validators import InputRequired

from common.utils import create_default_status_mappings
from connectors.jira import jira_core
from connectors.jira.jira_sync import JiraSync
from database import db
from structure.auth import User, Role, UserTeam, TeamRoleEnum
from structure.events import IssueSnapshot, Sprint
from structure.organization import Team
from structure.measurements import THCQuestion, THCMeasurement
from structure.measurements import OTMeasurement
from structure.project import (
    Activity,
    JiraProject,
    StatusCategoryStatusMapping,
    StatusCategory,
)
from views.cadmin import UploadDataView
from celery.result import AsyncResult


"""
Add pages for managing SQLAlchemy models
    For a SQLAlchemy-model `MyModel`, you can easily create an admin view
    which provides CRUD-functionality like this:
        mymodel_view = ModelView(MyModel, db_session)
    You can then automatically create a menu link in the NavBar with:
        admin.add_view(mymodel_view)
    Using the parameter `name`, you can give the menu-link a name and with
        `category`, you can add it to a sub-menu.
"""


class CheckSuperuserRoleMixin:
    def is_accessible(self):
        return current_user.is_superadmin

    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for("security.login", next=request.url))


# User


class UserTeamInlineModelForm(InlineFormAdmin):
    form_columns = [
        "id",
        "team",
        "role",
    ]

    form_overrides = dict(role=Select2Field, team=QuerySelectField,)
    form_args = dict(
        team=dict(validators=[InputRequired()], query_factory=lambda: Team.query),
        role=dict(choices=[(i.value, i.title) for i in TeamRoleEnum]),
    )


class UserAdmin(CheckSuperuserRoleMixin, ModelView):
    form_columns = [
        "email",
        "first_name",
        "last_name",
        "roles",
    ]
    column_list = ["email", "first_name", "last_name", "roles", "last_login_at"]

    column_default_sort = ("last_login_at", True)
    page_size = 1000

    column_auto_select_related = True

    inline_models = [
        UserTeamInlineModelForm(UserTeam),
    ]

    def scaffold_form(self):
        form_class = super().scaffold_form()

        form_class.password2 = PasswordField("New Password")
        return form_class

    def on_model_change(self, form, model, is_created):
        if model.password2:
            model.password = encrypt_password(model.password2)


class TeamMembersInlineModelForm(InlineFormAdmin):
    form_columns = [
        "id",
        "user",
        "role",
    ]

    form_overrides = dict(role=Select2Field, user=QuerySelectField,)
    form_args = dict(
        user=dict(validators=[InputRequired()], query_factory=lambda: User.query),
        role=dict(choices=[(i.value, i.title) for i in TeamRoleEnum]),
    )


class TeamModelView(ModelView):
    column_searchable_list = ["code", "name"]
    form_excluded_columns = ["activities"]

    inline_models = [
        TeamMembersInlineModelForm(UserTeam),
    ]

    @property
    def can_create(self):
        return current_user.is_superadmin

    @property
    def can_delete(self):
        return current_user.is_superadmin

    def get_query(self):
        if current_user.is_superadmin:
            return super().get_query()

        return (
            super().get_query().filter(Team.team_id.in_(current_user.writable_team_ids))
        )

    def get_one(self, id):  # pylint: disable=redefined-builtin
        query = self.get_query()
        return query.filter(Team.team_id == id).one()

    def get_count_query(self):
        return self.get_query().with_entities(func.count(Team.team_id))

    def is_accessible(self):
        return current_user.is_superadmin or current_user.writable_teams.count()


# Reference data


class THCQuestionModelView(CheckSuperuserRoleMixin, ModelView):
    column_searchable_list = ["topic"]
    column_filters = ["deck"]


class ActivityModelView(CheckSuperuserRoleMixin, ModelView):
    column_searchable_list = ["activity_name"]


# Measurements


class MeasurementModelView(ModelView):
    column_exclude_list = ["measurement_id"]
    form_excluded_columns = ["measurement_id"]
    column_filters = ["measurement_date", "team"]
    column_searchable_list = []


class THCResultForm1(form.Form):
    team = QuerySelectField("Team", [InputRequired()])
    session_name = StringField("Session Name", [InputRequired()])
    date = DateTimeField("Session Date", [InputRequired()])
    deck = Select2Field("Question Deck", [InputRequired()])
    form_step = HiddenField(default=1)


class THCMeasurementModelView(CheckSuperuserRoleMixin, MeasurementModelView):
    column_filters = MeasurementModelView.column_filters + ["session_name"]
    column_searchable_list = MeasurementModelView.column_searchable_list + [
        "question.topic"
    ]
    list_template = "admin/model/thc_measurement_list.html"

    def get_thc_result_create_1_form(self):
        form = THCResultForm1(get_form_data())
        form.team.query = current_user.readable_teams
        form.deck.choices = [
            (d[0], d[0]) for d in db.session.query(THCQuestion.deck).distinct()
        ]
        return form

    @expose("/bulk_new/", methods=("GET", "POST"))
    def bulk_create_view(self):
        return_url = self.get_url(".index_view")
        if not self.can_create:
            return redirect(return_url)

        form = self.get_thc_result_create_1_form()
        form_data = get_form_data()

        if request.method == "POST" and form_data:
            if form_data.get("form_step") == "1":
                # store
                form = self.get_thc_result_create_1_form()
                if self.validate_form(form):
                    session["thc_form_1_data"] = form_data
                    q_list = THCQuestion.query.filter_by(deck=form_data["deck"]).all()
                    return self.render("cadmin/thc_result_create_2.html", q_list=q_list)

            elif form_data.get("form_step") == "2":
                # create objects
                try:
                    prev_form_data = session.pop("thc_form_1_data")
                except KeyError:
                    # display step 1
                    pass
                else:
                    q_list = THCQuestion.query.filter_by(
                        deck=prev_form_data["deck"]
                    ).all()
                    for i in range(1, len(q_list) + 1):
                        measurement_data = dict(
                            question_id=form_data[f"q_{i}"],
                            result_red=form_data[f"red_{i}"],
                            result_yellow=form_data[f"yellow_{i}"],
                            result_green=form_data[f"green_{i}"],
                        )
                        obj = THCMeasurement(
                            measurement_date=prev_form_data["date"],
                            session_name=prev_form_data["session_name"],
                            team_id=prev_form_data["team"],
                            **measurement_data,
                        )
                        db.session.add(obj)
                    try:
                        db.session.commit()
                        flash(
                            f"Successfully recorded {prev_form_data['session_name']}",
                            "success",
                        )
                    except:
                        err_msg = f"Failed to record {prev_form_data['session_name']}"
                        current_app.logger.error(traceback.format_exc())
                        current_app.logger.error(err_msg)
                        flash(err_msg, "error")
                    return redirect(return_url)

        form = self.get_thc_result_create_1_form()
        template = "cadmin/thc_result_create_1.html"
        return self.render(template, form=form, return_url=return_url)


# Configurations


class StatusCategoryStatusMappingModelView(CheckSuperuserRoleMixin, ModelView):
    column_searchable_list = ["activity.activity_name"]
    column_editable_list = ["status", "status_category"]
    list_template = "admin/model/status_category_status_mapping_list.html"

    @expose("/load_jira_mappings/")
    def load_jira_mappings(self):
        return_url = get_redirect_target() or self.get_url(".index_view")
        try:
            current_app.logger.info("Attempting to connect to jira")
            jira = jira_core.connect()
        except Exception as e:
            status = "Jira not configured"
            flash(status, "error")
            current_app.logger.error(f"{status}: {e}")
        else:
            if jira is not None:
                # load default status mapping
                create_default_status_mappings(
                    {d.name: d.statusCategory.name for d in jira.statuses()}
                )
            else:
                flash("Jira failed to connect", "error")
            return redirect(return_url)


class ConfigureJiraConnectionView(CheckSuperuserRoleMixin, ModelView):
    can_create = False
    can_delete = False
    can_edit = False
    column_default_sort = "team.name"
    column_editable_list = ("jira_project",)
    column_searchable_list = (
        "team.name",
        "jira_project.project_key",
        "jira_project.project_name",
    )
    column_sortable_list = (("team", "team.name"),)
    list_template = "admin/model/team_activity_list.html"

    @expose("/")
    def index_view(self):
        activities = Activity.query.filter(Activity.jira_project != None).all()
        for activity in activities:
            self.task_status(activity.activity_id)

        return super().index_view()

    @expose("/load_projects/")
    def load_projects(self):
        return_url = get_redirect_target() or self.get_url(".index_view")
        try:
            current_app.logger.info("Attempting to connect to jira")
            jira = jira_core.connect()
        except Exception as e:
            status = "Jira not configured"
            current_app.logger.error(f"{status}: {e}")
            flash(status, "error")
        else:
            if jira is not None:
                # load projects
                projects = jira.projects()
                for project in projects:
                    # create or update in case of change in Jira.
                    stmt = (
                        pg_insert(JiraProject)
                        .values(project_key=project.key, project_name=project.name)
                        .on_conflict_do_update(
                            constraint="uq_jira_projects_project_key",
                            set_=dict(project_name=project.name),
                        )
                    )
                    db.session.execute(stmt)
                    db.session.commit()
                status = f"{len(projects)} project/s loaded successfully."
                current_app.logger.info(f"{status}")
                flash(status, "success")
            else:
                flash("Jira failed to connect", "error")
        return redirect(return_url)

    @expose("/delete_sprints_and_issues/")
    def delete_sprints_and_issues(self):
        return_url = get_redirect_target() or self.get_url(".index_view")
        model_id = get_mdict_item_or_list(request.args, "id")
        model = self.get_one(model_id)
        try:
            sprints = (
                Sprint.query.filter(Sprint.activity == model)
                .with_entities(Sprint.sprint_id)
                .all()
            )
            issue_count = IssueSnapshot.query.filter(
                IssueSnapshot.sprint_id.in_(sprints)
            ).delete(synchronize_session=False)
            db.session.commit()
            sprint_count = Sprint.query.filter(Sprint.activity == model).delete()
            db.session.commit()
            message = (
                f"Deleted {sprint_count} sprints with {issue_count} issue snapshots."
            )
            current_app.logger.info(message)
            flash(message, "success")
        except Exception:
            current_app.logger.error(traceback.format_exc())
            current_app.logger.error("Failed to delete sprints and issue snapshots")
            flash("Deleting sprints and issue snapshots failed", "error")
        return redirect(return_url)

    @expose("/sync_project_sprints_without_issues/", methods=("GET",))
    def sync_project_sprints_without_issues(self):
        return_url = get_redirect_target() or self.get_url(".index_view")
        model_id = get_mdict_item_or_list(request.args, "id")
        model = self.get_one(model_id)
        if not model.jira_project:
            flash("No Jira Project assigned to Activity", "error")
            return redirect(return_url)

        try:
            # synchronous sync
            current_app.logger.info(
                f"Syncing all sprints (without issues) of project {model.jira_project.project_key}"
            )
            from tasks.jira import (  # pylint: disable=import-outside-toplevel
                sync_all_sprints_without_issues,
            )

            result_only_sprints = sync_all_sprints_without_issues.delay(model_id)
            result_only_sprints.get()

            flash("Project sprints successfully synced.", "success")
        except Exception as e:
            logging.error(f"Sync project error: {e}")
            flash("Project sprints not synced.", "error")
        return redirect(return_url)

    @expose("/sync_project/", methods=("GET",))
    def sync_project(self):
        return_url = get_redirect_target() or self.get_url(".index_view")
        model_id = get_mdict_item_or_list(request.args, "id")
        model = self.get_one(model_id)
        if not model.jira_project:
            flash("No Jira Project assigned to Activity", "error")
            return redirect(return_url)

        try:
            # synchronous sync
            current_app.logger.info(
                f"Syncing all sprints (without issues) of project {model.jira_project.project_key}"
            )
            from tasks.jira import (  # pylint: disable=import-outside-toplevel
                sync_activity_past_data,
                sync_all_sprints_without_issues,
            )

            task = self._get_task_by_activity(model_id)

            # check if a task is currently running
            if not task or task.state == "PENDING":
                result_only_sprints = sync_all_sprints_without_issues.delay(model_id)
                result_only_sprints.get()
                current_app.logger.info(
                    f"Syncing sprint issues of project {model.jira_project.project_key}"
                )
                result_with_issues = sync_activity_past_data.apply_async(
                    args=[model_id]
                )
                task_session_key = f"sync_project_task_{model_id}"
                session[task_session_key] = result_with_issues.task_id
                flash("Sprints details synced. Sprint issues started syncing.", "info")
            else:
                current_app.logger.info(
                    f"Syncing in progress for Activity {activity_id}"
                )
        except Exception as e:
            current_app.logger.error(traceback.format_exc())
            current_app.logger.error(f"Sync project error: {e}")
            flash("Project not synced.", "error")
        return redirect(return_url)

    def _get_task_by_activity(self, activity_id):
        from tasks.jira import (  # pylint: disable=import-outside-toplevel
            sync_activity_past_data,
        )

        task_session_key = f"sync_project_task_{activity_id}"
        task_id = session.get(task_session_key)
        if task_id:
            return sync_activity_past_data.AsyncResult(task_id)
        else:
            return None

    @expose("/sync_project/status/")
    def task_status(self, activity_id=None):
        if not activity_id:
            activity_id = get_mdict_item_or_list(request.args, "activity_id")
        task = self._get_task_by_activity(activity_id)
        if task:
            if task.state in ("PENDING", "SENT"):
                # job did not start yet
                response = {
                    "state": task.state,
                    "current": 0,
                    "total": 1,
                    "status": "Pending...",
                }
            elif task.state != "FAILURE":
                response = {
                    "state": task.state,
                    "current": task.info.get("current", 0),
                    "total": task.info.get("total", 1),
                    "status": task.info.get("status", ""),
                }
            else:
                # something went wrong in the background job
                response = {
                    "state": task.state,
                    "current": 1,
                    "total": 1,
                    "status": str(task.info),  # this is the exception raised
                }

            # clear results
            if task.state in ("FAILURE", "SUCCESS"):
                task.forget()
                session.pop(f"sync_project_task_{activity_id}", None)
                flash(
                    f"Sprint issues successfully synced for Activity {activity_id}",
                    "success",
                )
        else:
            response = {
                "state": "ERROR",
                "current": 1,
                "total": 1,
                "status": f"No task found for Activity {activity_id}",
            }
        return jsonify(response)


# Initialize flask admin


class CustomAdminIndexView(AdminIndexView):
    @expose("/")
    @login_required
    def index(self, *args, **kwargs):
        return super().index(*args, **kwargs)


CATEGORY_LABEL_TEAM_DATA = "Team data"
CATEGORY_LABEL_REFERENCE_DATA = "Reference data"
CATEGORY_LABEL_CONFIGURATION = "Configuration"

admin = Admin(
    name="Team Metrics Visualizer admin",
    template_mode="bootstrap3",
    index_view=CustomAdminIndexView(),
)

## Team data
# TODO: Sprint progress
# TODO: Sprint progress upload
# TODO(#80): OKR progress
# TODO: Overtime
admin.add_view(
    UploadDataView(
        name="Overtime Data Upload",
        category=CATEGORY_LABEL_TEAM_DATA,
        endpoint="overtime",
        connector="overtime",
    )
)

admin.add_view(
    THCMeasurementModelView(
        THCMeasurement,
        db.session,
        category=CATEGORY_LABEL_TEAM_DATA,
        name="Team Health Check",
    )
)

## Reference data
admin.add_view(
    UserAdmin(
        User,
        db.session,
        name="Users",
        category=CATEGORY_LABEL_REFERENCE_DATA,
        endpoint="manage-users",
    )
)

admin.add_view(
    TeamModelView(
        Team, db.session, name="Teams", category=CATEGORY_LABEL_REFERENCE_DATA
    )
)

admin.add_view(
    THCQuestionModelView(
        THCQuestion,
        db.session,
        category=CATEGORY_LABEL_REFERENCE_DATA,
        name="Team Health Check: Deck & Topics",
    )
)

## Configuration
# TODO: GitHub: Map repos to teams
admin.add_view(
    ConfigureJiraConnectionView(
        Activity,
        db.session,
        category=CATEGORY_LABEL_CONFIGURATION,
        name="JIRA: Connection & Manual sync",
    )
)

admin.add_view(
    StatusCategoryStatusMappingModelView(
        StatusCategoryStatusMapping,
        db.session,
        category=CATEGORY_LABEL_CONFIGURATION,
        name="JIRA: Status Category mapping",
    )
)


admin.add_link(MenuLink("Dashboards", url="/dash/"))
