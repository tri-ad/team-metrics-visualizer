# How to contribute

Contributing to this project is quite straightforward and works like this:

1. Fork this repo.
1. Follow the instructions in `README.md` or in the docs to set up your development environment.
1. Either choose an issue from the list or create a new issue. Please make a comment indicating that you want to work on this issue.
1. Make some changes!
1. Create a pull request, targeting `master`.

## Table of contents

- [Pull requests](#Pull-requests)
- [Commit rules](#Commit-rules)
- [Code guidelines](#Code-guidelines)
- [IDE configuration](#IDE-configuration)
- [Folder structure](#Folder-structure)
- [How to write tests](#How-to-write-tests)
- [Documentation](#Documentation)
- [Database migrations](#Database-migrations)
- [Styling](#Styling)

## Pull requests

When creating pull request, please make sure the following:

- Make sure you have the most recent version of `master` and rebase before creating the pull request.
- Make sure all tests pass locally.
- Please include only one commit in your pull request. Squash if necessary.

## Commit rules

Please format all of your commits according to the [Conventional Commits](https://www.conventionalcommits.org/) specification. Commits should be self-contained and related to at least one issue from the issue-list. Please mention the issue-ID at the end of the commit message. If there is no issue for your change, feel free to create one.

## Code guidelines

The code is automatically checked in pre-commit hooks via `pre-commit`.

- `black` is used for autoformatting
- `pylint` is used for linting

To autoformat and lint staged git files run: `pipenv run pre-commit run`. After that you may need to fix linter warnings and `git add` fixed and reformatted files.

You can have a look at `pylintrc` to see which linter checks we disabled.

## IDE configuration

We use Visual Studio Code for development, but you are of course free to use any IDE or editor you would like. If you use Visual Studio Code, we recommend to add the following to your workspace configuration:

```json
    "python.autoComplete.extraPaths": [
        "./tmv"
    ],
    "python.formatting.provider": "black",
    "python.linting.pylintEnabled": true,
    "python.linting.enabled": true,
    "python.testing.pytestEnabled": true,
    "python.testing.nosetestsEnabled": false,
    "python.testing.unittestEnabled": false,
    "python.testing.pytestArgs": [
        "tmv/test"
    ],
    "python.languageServer": "Microsoft",
    "editor.rulers": [
        88
    ]
```

We recommend to install the following extensions to make development easier:

- [Python Docstring Generator](https://marketplace.visualstudio.com/items?itemName=njpwerner.autodocstring) (with setting `"autoDocstring.docstringFormat": "sphinx"`)
- [reStructuredText](https://marketplace.visualstudio.com/items?itemName=lextudio.restructuredtext)
- [markdownlint](https://marketplace.visualstudio.com/items?itemName=DavidAnson.vscode-markdownlint)

And of course [Microsoft's Python-extension](https://marketplace.visualstudio.com/items?itemName=ms-python.python).

## Folder structure

Structure below shows all folders up to depth 3.

```text
.
├── CONTRIBUTING.md     # This file.
├── docs                # Documentation (as rst)
│   └── _static         # Assets used in documentation
├── tmv                 # The app's sourcecode
│   ├── auth            # Authentication & secrets
│   ├── aws             # Interaction with AWS (if required)
│   ├── common          # Code shared in several places
│   ├── connectors      # Used to read data from various sources
│   │   ├── TeamHealthCheck # ... for team health check
│   │   ├── jira            # ... JIRA
│   │   └── overtime        # ... and Excel-import of worktime data
│   ├── dashboards      # Dashboard-classes using visuals and slicers
│   ├── database        # Database interaction
│   ├── helpers         # Helper-functions
│   ├── migrations      # Database migrations using flask-migrate
│   │   └── versions
│   ├── slicers         # Slicers (filters) for use in dashboards
│   ├── static          # CSS, JS, logo, etc.
│   │   ├── admin
│   │   └── dash
│   ├── structure       # Database models
│   ├── style           # Styles using Sass
│   │   └── vendors
│   ├── tasks           # Celery-tasks for data download
│   ├── templates       # Templates for views which are not visuals
│   │   ├── admin
│   │   ├── cadmin
│   │   └── security
│   ├── test            # Tests
│   │   └── resources
│   ├── test_coverage   # Coverage report stored here if you create it
│   ├── tmv_dash_components -> ../tmv_dash_components/tmv_dash_components/
│   ├── tools           # A CLI-tool to mass-import data
│   ├── views           # Views, mainly for admin area
│   └── visuals         # Visuals to be used in dashboards
├── tmv-docker-dev      # docker-compose for dev-setup
├── tmv-docker-prod     # docker-compose for deployment
│   └── app
└── tmv_dash_components # Custom dash-components used in the tool
    ├── src
    │   ├── demo
    │   └── lib
    ├── tests
    └── tmv_dash_components

43 directories
```

Built with `tree . -d -I "__pycache__|node_modules|temp_uploads|_build" -L 3`.

## How to write tests

We are using the testing-framework `pytest` for testing. Please have a brief look at [the documentation](https://docs.pytest.org/en/latest/) and especially at the [part on fixtures](https://docs.pytest.org/en/latest/fixture.html).

- All tests should be put in the directory `test/`.
- If you need test data (text files etc.), you can put it in `test/resources/`.
- Have a look at `test/conftest.py` for some convenient globally available fixtures you can use.

### Flask app tests

The fixture `app` (located in `test/conftest.py`) provides you with a flask app instance and a database for each test. `pytest-flask-sqlalchemy` is used to reset the database state after each test. When a test involves the flask app or db-session, you need to use the `app`-fixture like so `def test_something(app)`.

The following will happen behind the scenes:

1. `_database_uri()` will try to get the the database URI from `TESTING_SQLALCHEMY_DATABASE_URI` environment variable or try to create a database with postfix `_test` as the app's default database.
1. `_app_and_db()` will establish a connection to the DB, then clean and migrate it.
1. `app()` will create a `db_session` via `pytest-flask-sqlalchemy` and mock `db.session`, so it resets the database state after each test.

## Documentation

We make use of [Sphinx](https://www.sphinx-doc.org/en/master/) for our documentation. We use `autodoc` using reStructuredText format.

### Building documentation

You can build the documentation locally by executing `make html` in folder `docs`. Generated html files will be in `_build/`. The start-page of the documentation is `index.html`.

## Database migrations

We use [Flask-Migrate](https://flask-migrate.readthedocs.io/en/latest/) to create migrations that apply data-model changes. Flask-Migrate helps you make sure that the code (the ORM actually) is aligned with the data you have on your DB.

### In case you have made changes to the data model

If you make changes to the data model, editing or creating tables or fields, make sure that you create a migration and apply it to the DB. Generated migration files should be verified manually, because not all changes are caught by Flask-Migrate.

```sh
# Create the migration file
flask db migrate -m "Migration message. It could be something like 'Added name field'"
# Apply the migration
flask db upgrade
```

### Other useful commands for flask migrate

- Show a list of revisions with `flask db history`
- Revert to previous revision with `flask db downgrade`
- Show the current DB revision with `flask db current`

## Styling

We use [Dash Bootstrap Components](https://dash-bootstrap-components.opensource.faculty.ai/) for most UI components.
We use [Bootstrap](https://getbootstrap.com/) with Sass to style them.
If you want to customize the style, edit the SCSS files at `tmv/style` and re-generate the CSS:

1. From the main project folder: `npm install` and `npm run build`.
1. Webpack will generate `main.css` and `main.js` files in `./tmv/static/dash` folder.

The generated files are included in the repo for convenience when installing the tool. If you modify them for your local installation, make sure to not include them in your pull request.
