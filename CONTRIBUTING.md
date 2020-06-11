# How to contribute
We follow _trunk-based development_. In order to contribute, please make a fork of this repository and work in your fork. When you are done, create a merge-request to the `master`-branch of this repository.
Each merge request should only contain one commit. Use fast-forward as merge-strategy and rebase if necessary.

All merge requests have to be reviewed by somebody in the team. After this, please ping @moritz.scholz to have a quick look.

## Commit guidelines
Commits should be self-contained. The tool must be able to run in each commit and all tests must pass. No line in the commit message should be longer than **72** characters. Commits related to issues must contain the issue-ID in the commit message. If there is no issue for the commit (for example if you fix a bug you just found), please create one except it does not make sense.
Because GitLab issues are referenced as `#n` (e.g. `#42` for issue number 42), we cannot start a line with the issue ID, because then it will be considered as a comment. In that case you can refer to it by writing "_Issue #42_".

Commit messages should follow the [Conventional Commits standard](https://www.conventionalcommits.org).

## Code guidelines

The code is automatically checked in pre-commit hooks via `pre-commit`.

- `black` is used for autoformatting
- `pylint` is used for linting

To autoformat and lint staged git files run: `pipenv run pre-commit run`

After that you need to fix linter warnings and `git add` fixed and reformatted files

### Using from terminal

To lint python files: `pipenv run pylint tmv/`

To autoformat python files: `pipenv run black tmv/`

## Folder structure
Structure below shows all folders and some key files.
```
.
├── CONTRIBUTING.md     <-- This file.
├── tmv-docker-prod     <-- Files for building docker images & docker-compose.
│   └── app             <-- tmv app's Dockerfile & requirements for python-env.
├── tmv-docker-dev      <-- Files for docker db for development.
├── tmv_dash_components <-- Custom Dash components.
└── tmv                 <-- Team Metrics visualizer app
    ├── auth                <-- Module for handling authentication.
    ├── aws                 <-- Module for calling AWS-services.
    ├── connectors          <-- Data connectors/importers go here.
    ├── ├── TeamHealthCheck <-- Importer for data from team health check.
    ├── ├── jira            <-- Connector to JIRA.
    ├── └── overtime        <-- Importer (future: connector) for overtime time-keeping.
    ├── dashboards          <-- Dashboards classes which combine several Visuals.
    ├── database            <-- DB-engine is initialized here (via SQLAlchemy).
    ├── file_handling       <-- Helper-functions for handling of files uploaded by user.
    ├── static              <-- Images, Scripts, CSS-files etc. Contains bootstrap-CSS.
    │   ├── TeamHealthCheck <-- Icons which can be used for team health check visual.
    │   ├── dash            <-- Assets for dash (currently: only favicon).
    │   └── scripts         <-- JavaScripts.
    ├── structure           <-- The data models are defined here.
    ├── style               <-- The source Sass files implementing the default theme are here.
    ├── templates           <-- Templates for usage with flask views. Has a folder for each section.
    │   ├── admin           <-- Templates for admin views.
    │   └── cadmin          <-- Templates for admin views which provide functionality outside Flask-Admin (for data upload etc.)
    ├── test                <-- All tests go here and should be named "test_*.py".
    │   └── resources       <-- Put sample data for the tests here.
    ├── tools               <-- CLI-tools can be found here.
    │   ├── db_tool.py      <-- CLI-tool to create database tables and import data.
    │   └── sample_data     <-- Data for import through CLI-tools to fill an empty database.
    ├── views               <-- Views for flask. Different file for each section.
    └── visuals             <-- Classes for visuals which go on dashboards are here.
```
Built with `tree . -d -I __pycache__`.

## How to write tests
We are using the testing-framework `pytest` for testing. Please have a brief look at [the documentation](https://docs.pytest.org/en/latest/) and especially at the [part on fixtures](https://docs.pytest.org/en/latest/fixture.html).
- All tests should be put in the directory 'test/'.
- If you need test data (text files etc.), you can put them in `test/resources`.
- Have a look at `test/conftest.py` for some globally available fixtures to use.

### Flask app tests
The fixture `app` (code is in `test/conftest.py`) provides you with a flask app instance and a migrated database for each test. `pytest-flask-sqlalchemy` is used to reset the database state after each test. When a test involves flask app or db session, you need to include `app` fixture via function arg `def test_something(app)` or via `@pytest.mark.usefixtures("app")`.

The following will happen behind the scenes:
1. `_database_uri()` will try to get DB URI from `TESTING_SQLALCHEMY_DATABASE_URI` env var or try to create a database with postfix `_test` for app's default DB.
1. `_app_and_db()` will establish a connection to the DB, then clean and migrate it.
1. `app()` will create a `db_session` via `pytest-flask-sqlalchemy` and mock `db.session`, so it resets the DB state after each test.

## Documentation
We make use of [Sphinx](https://www.sphinx-doc.org/en/master/) for our documentation. We use `autodoc` using reStructuredText format.

### Generating docs
1. `cd docs`
2. `make html`
3. Generated html files will be in `_build/`. Main page is `index.html`.
