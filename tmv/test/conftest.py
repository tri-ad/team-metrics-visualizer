import tempfile
import pytest
from common.exceptions import MissingConfigurationError
from database import db as flask_app_db
from flask_migrate import upgrade
from sqlalchemy import create_engine
from sqlalchemy.exc import ProgrammingError
from flask_sqlalchemy import SQLAlchemy
import time
from app import create_app, TmvConfig, create_tmv_config_from_env
from structure.organization import Team
import os
from urllib.parse import urlparse
from psycopg2.extensions import AsIs


def recreate_postgres_db(db_uri, db_name):
    engine = create_engine(db_uri)
    with engine.connect() as conn:
        conn.execution_options(isolation_level="AUTOCOMMIT")
        try:
            conn.execute("DROP DATABASE %s", (AsIs(db_name),))
        except ProgrammingError:
            pass  # does not exist
        conn.execute("CREATE DATABASE %s", (AsIs(db_name),))


@pytest.fixture(scope="session")
def _database_uri():
    """Use db from TESTING_SQLALCHEMY_DATABASE_URI env var or
    try to create db for SQLALCHEMY_DATABASE_URI with postfix "_test"
    """

    TESTING_SQLALCHEMY_DATABASE_URI = os.getenv("TESTING_SQLALCHEMY_DATABASE_URI")

    if TESTING_SQLALCHEMY_DATABASE_URI:
        testing_database_uri = TESTING_SQLALCHEMY_DATABASE_URI
    else:
        config = create_tmv_config_from_env()

        if not config.SQLALCHEMY_DATABASE_URI:
            raise MissingConfigurationError(
                "DB is not configured. Set TESTING_SQLALCHEMY_DATABASE_URI env var "
                "to specify Postgres DB for testing or set SQLALCHEMY_DATABASE_URI "
                "env var to specify app DB, so it will attempt to create a database "
                'with "_test" postfix'
            )

        testing_database_uri = config.SQLALCHEMY_DATABASE_URI + "_test"

        db_name = urlparse(testing_database_uri).path.lstrip("/")
        recreate_postgres_db(config.SQLALCHEMY_DATABASE_URI, db_name)

    yield testing_database_uri


@pytest.fixture(scope="session")
def _temp_uploads_folder():
    with tempfile.TemporaryDirectory() as tmpdirname:
        yield tmpdirname


@pytest.fixture(scope="session")
def _app_and_db(_database_uri, _temp_uploads_folder):
    app = create_app(
        TmvConfig(
            SECRET_KEY="testing_secret_key",
            SECURITY_PASSWORD_SALT="testing_password_salt",
            SQLALCHEMY_DATABASE_URI=_database_uri,
            TEMP_UPLOADS_FOLDER=_temp_uploads_folder,
            JIRA_FIELD_SPRINT="Sprint",
            JIRA_FIELD_STORYPOINTS="Story Points",
        ),
        config_override=dict(
            TESTING=True,
            SECURITY_HASHING_SCHEMES=["hex_md5"],
            SECURITY_DEPRECATED_HASHING_SCHEMES=[],
            SECURITY_PASSWORD_HASH="plaintext",  # to reduce user creation time
        ),
    )

    with app.app_context():
        print("waiting for DB to be up")
        MAX_CONNECTION_ATTEMPTS = 5
        connected = False
        last_exc = None
        for _ in range(MAX_CONNECTION_ATTEMPTS):
            try:
                flask_app_db.drop_all()
                upgrade(revision="head")
                connected = True
            except Exception as e:
                last_exc = e
                time.sleep(1)
            else:
                break
        if not connected:
            raise last_exc
        yield app


@pytest.fixture(scope="session")
def _db(_app_and_db):
    return SQLAlchemy(app=_app_and_db)


@pytest.fixture(scope="function")
def app(_app_and_db, db_session):
    yield _app_and_db


@pytest.fixture(scope="function")
def team(db_session):
    team = Team(parent_team=None, code="ABC", name="Team ABC")
    flask_app_db.session.add(team)
    flask_app_db.session.commit()
    return team
