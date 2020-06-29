import logging
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

import dash
import flask
from authlib.integrations.flask_client import OAuth
from dotenv import load_dotenv
from flask_security import Security

from common.dash_callbacks import register_common_callbacks
from auth import DashFlaskSecurityAuth
from dash_layout import init_tabs_for_navbar, layout
from dashboards.Burnup import BurnupDashboardController
from dashboards.LongTermHealth import LongTermHealthDashboardController
from dashboards.TeamHealthCheck import TeamHealthCheckDashboardController
from dashboards.Worktime import WorktimeDashboardController
from dashboards.CumulativeFlow import CumulativeFlowDashboardController
from database import db, migrate
from structure.auth import CustomAnonymousUser, user_datastore
from views.admin import admin
from views.user import user

BASE_DIR = Path(__file__).resolve().parent.parent
DASHBOARD_PREFIX = "/dash/"

if __name__ == "__main__":
    print("Please create .env file and start dev server via `flask run --port 8050`")
    sys.exit(1)


@dataclass
class TmvConfig:
    SECRET_KEY: str
    SQLALCHEMY_DATABASE_URI: str
    TEMP_UPLOADS_FOLDER: str

    SECURITY_PASSWORD_SALT: str
    SECURITY_REGISTERABLE: bool = False

    CELERY_BROKER_URL: str = None
    CELERY_RESULT_BACKEND: str = None

    JIRA_OAUTH_LOC: str = None
    JIRA_SERVER: str = None
    JIRA_CONSUMER_KEY: str = None
    JIRA_CONSUMER_SECRET: str = None
    JIRA_ACCESS_TOKEN: str = None
    JIRA_ACCESS_SEC: str = None
    JIRA_RSA_PEM: str = None

    JIRA_FIELD_SPRINT: str = None
    JIRA_FIELD_STORYPOINTS: str = None

    OKTA_ORG_BASEURL: str = None
    OKTA_CLIENT_ID: str = None
    OKTA_CLIENT_SECRET: str = None

    AWS_REGION: str = None

    DEV_MODE: bool = False


def create_tmv_config_from_env() -> TmvConfig:
    load_dotenv()

    SQLALCHEMY_DATABASE_URI = os.getenv("SQLALCHEMY_DATABASE_URI")

    if not SQLALCHEMY_DATABASE_URI:
        POSTGRES_USER = os.environ["POSTGRES_USER"]
        POSTGRES_PASSWORD = os.environ["POSTGRES_PASSWORD"]
        POSTGRES_HOST = os.environ["POSTGRES_HOST"]
        POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
        POSTGRES_DB = os.environ["POSTGRES_DB"]
        SQLALCHEMY_DATABASE_URI = (
            f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@"
            f"{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
        )

    CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL")
    CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND")

    if not CELERY_BROKER_URL and not CELERY_RESULT_BACKEND:
        try:
            RABBITMQ_DEFAULT_USER = os.environ["RABBITMQ_DEFAULT_USER"]
            RABBITMQ_DEFAULT_PASS = os.environ["RABBITMQ_DEFAULT_PASS"]
            RABBITMQ_HOST = os.environ["RABBITMQ_HOST"]
            RABBITMQ_PORT = os.environ["RABBITMQ_PORT"]

            CELERY_BROKER_URL = (
                f"amqp://{RABBITMQ_DEFAULT_USER}:{RABBITMQ_DEFAULT_PASS}@"
                f"{RABBITMQ_HOST}:{RABBITMQ_PORT}"
            )
            CELERY_RESULT_BACKEND = (
                f"rpc://{RABBITMQ_DEFAULT_USER}:{RABBITMQ_DEFAULT_PASS}@"
                f"{RABBITMQ_HOST}:{RABBITMQ_PORT}"
            )
        except KeyError:
            logging.warning("Celery not configured properly.")

    return TmvConfig(
        DEV_MODE=os.getenv("TMV_DEV") == "1",
        SECRET_KEY=os.environ["FLASK_SECRET_KEY"],
        SQLALCHEMY_DATABASE_URI=SQLALCHEMY_DATABASE_URI,
        TEMP_UPLOADS_FOLDER=os.environ["TEMP_UPLOADS_FOLDER"],
        SECURITY_PASSWORD_SALT=os.environ["SECURITY_PASSWORD_SALT"],
        SECURITY_REGISTERABLE=os.getenv("SECURITY_REGISTERABLE") == "1",
        OKTA_ORG_BASEURL=os.getenv("OKTA_ORG_BASEURL"),
        OKTA_CLIENT_ID=os.getenv("OKTA_CLIENT_ID"),
        OKTA_CLIENT_SECRET=os.getenv("OKTA_CLIENT_SECRET"),
        AWS_REGION=os.getenv("AWS_REGION"),
        JIRA_OAUTH_LOC=os.getenv("JIRA_OAUTH_LOC"),
        JIRA_SERVER=os.getenv("JIRA_SERVER"),
        JIRA_CONSUMER_KEY=os.getenv("JIRA_CONSUMER_KEY"),
        JIRA_CONSUMER_SECRET=os.getenv("JIRA_CONSUMER_SECRET"),
        JIRA_ACCESS_TOKEN=os.getenv("JIRA_ACCESS_TOKEN"),
        JIRA_ACCESS_SEC=os.getenv("JIRA_ACCESS_SEC"),
        JIRA_RSA_PEM=os.getenv("JIRA_RSA_PEM"),
        JIRA_FIELD_SPRINT=os.getenv("JIRA_FIELD_SPRINT", "Sprint"),
        JIRA_FIELD_STORYPOINTS=os.getenv("JIRA_FIELD_STORYPOINTS", "Story Points"),
        CELERY_BROKER_URL=CELERY_BROKER_URL,
        CELERY_RESULT_BACKEND=CELERY_RESULT_BACKEND,
    )


def create_app(
    config: Optional[TmvConfig] = None, config_override: Optional[Dict] = None
):
    if config is None:
        config = create_tmv_config_from_env()

    if config_override is None:
        config_override = {}

    """ Set up logging
        Logging uses the built-in logging-module, see the Python docs for details.
        If you want to log something, please use one of the following methods,
        depending on the level you want to log.
        logging.debug()
        logging.info()
        logging.warning()
        logging.error()
        logging.critical()

        You can configure from which level log messages get output by modifying
        the parameter `level` in the lines below.

        You can add further handlers (for example for sending e-mails on critical
        errors) to the logging system if you want. Make sure to always log using
        an appropriate level to not clutter the logs with meaningless messages.
    """
    log_level = logging.DEBUG if config.DEV_MODE else logging.WARNING

    logging.basicConfig(
        format="[%(asctime)s] %(levelname)s in %(module)s: %(message)s",
        level=log_level,
        handlers=[logging.StreamHandler()],
    )

    logging.info("Dev mode is " + ("on" if config.DEV_MODE else "off") + ".")

    # Initialize flask app
    app = flask.Flask(__name__, template_folder=str(BASE_DIR / "tmv" / "templates"),)

    app.url_map.strict_slashes = False

    app.config.from_mapping(
        SECRET_KEY=config.SECRET_KEY,
        SQLALCHEMY_DATABASE_URI=config.SQLALCHEMY_DATABASE_URI,
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        TEMP_UPLOADS_FOLDER=str(BASE_DIR / config.TEMP_UPLOADS_FOLDER),
        SECURITY_PASSWORD_SALT=config.SECURITY_PASSWORD_SALT,
        SECURITY_REGISTERABLE=config.SECURITY_REGISTERABLE,
        SECURITY_SEND_REGISTER_EMAIL=False,  # TODO: requires mail setup
        SECURITY_USER_IDENTITY_ATTRIBUTES=["email"],
        SECURITY_PASSWORD_HASH="pbkdf2_sha512",
        SECURITY_TRACKABLE=True,
        SECURITY_FORGOT_PASSWORD_TEMPLATE="security/custom_forgot_password.html",
        SECURITY_LOGIN_USER_TEMPLATE="security/custom_login_user.html",
        SECURITY_REGISTER_USER_TEMPLATE="security/custom_register_user.html",
        SECURITY_RESET_PASSWORD_TEMPLATE="security/custom_reset_password.html",
        SECURITY_CHANGE_PASSWORD_TEMPLATE="security/custom_change_password.html",
        SECURITY_SEND_CONFIRMATION_TEMPLATE="security/custom_send_confirmation.html",
        SECURITY_SEND_LOGIN_TEMPLATE="security/custom_send_login.html",
        OKTA_ORG_BASEURL=config.OKTA_ORG_BASEURL,
        OKTA_CLIENT_ID=config.OKTA_CLIENT_ID,
        OKTA_CLIENT_SECRET=config.OKTA_CLIENT_SECRET,
        AWS_REGION=config.AWS_REGION,
        JIRA_OAUTH_LOC=config.JIRA_OAUTH_LOC,
        JIRA_SERVER=config.JIRA_SERVER,
        JIRA_CONSUMER_KEY=config.JIRA_CONSUMER_KEY,
        JIRA_CONSUMER_SECRET=config.JIRA_CONSUMER_SECRET,
        JIRA_ACCESS_TOKEN=config.JIRA_ACCESS_TOKEN,
        JIRA_ACCESS_SEC=config.JIRA_ACCESS_SEC,
        JIRA_RSA_PEM=config.JIRA_RSA_PEM,
        JIRA_FIELD_SPRINT=config.JIRA_FIELD_SPRINT,
        JIRA_FIELD_STORYPOINTS=config.JIRA_FIELD_STORYPOINTS,
        FLASK_ADMIN_SWATCH="simplex",
        CELERY_BROKER_URL=config.CELERY_BROKER_URL,
        CELERY_RESULT_BACKEND=config.CELERY_RESULT_BACKEND,
    )
    app.config.update(config_override)

    db.init_app(app)
    migrate.init_app(app, db, directory=str(BASE_DIR / "./tmv/migrations/"))

    app.security = Security(app, user_datastore, anonymous_user=CustomAnonymousUser)

    app.oauth = OAuth(app)
    if config.OKTA_ORG_BASEURL:
        app.oauth.register(
            "okta",
            server_metadata_url=(
                config.OKTA_ORG_BASEURL
                + "/oauth2/default/.well-known/openid-configuration"
            ),
            client_kwargs={"scope": "openid profile email"},
        )

    # Create directories if they not already exist.
    FOLDERS_TO_CREATE = {
        app.config["TEMP_UPLOADS_FOLDER"],
    }
    for folder in FOLDERS_TO_CREATE:
        os.makedirs(folder, exist_ok=True)

    # Register flask pages
    # Add your page here by creating a blueprint in /views, importing it and
    #   registering it via `app.register_blueprint`.
    admin.init_app(app)
    app.register_blueprint(user)

    dash_app = dash.Dash(
        __name__,
        server=app,
        # The route to put dash in:
        routes_pathname_prefix=DASHBOARD_PREFIX,
        external_stylesheets=[
            (
                "https://fonts.googleapis.com/css2?"
                "family=Roboto:wght@300;400;500;700&display=swap"
            ),
        ],
        assets_folder="static/dash",
        assets_url_path="/static/dash",
        suppress_callback_exceptions=True,
        meta_tags=[
            {"name": "viewport", "content": "width=device-width, initial-scale=1"}
        ],
    )
    dash_app.title = "Team Metrics Visualizer"

    DashFlaskSecurityAuth(dash_app)

    if config.DEV_MODE:
        dash_app.enable_dev_tools()

    # Initialize dashboards.
    # Add your dashboard here by creating an instance and adding it to TABS
    dashboards = [
        TeamHealthCheckDashboardController(),
        LongTermHealthDashboardController(),
        BurnupDashboardController(),
        CumulativeFlowDashboardController(),
        WorktimeDashboardController(),
    ]

    def layout_fn(*args, **kwargs):
        if flask.has_app_context() and flask.has_request_context():
            dash_app._cached_layout = None  # pylint: disable=protected-access
            return layout(dashboards, DASHBOARD_PREFIX)

    dash_app.layout = layout_fn
    init_tabs_for_navbar(dash_app, dashboards, DASHBOARD_PREFIX)

    register_common_callbacks(dash_app)

    return app
