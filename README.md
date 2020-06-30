# Team Metrics Visualizer

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
![CI-Pipeline status](https://github.com/tri-ad/team-metrics-visualizer/workflows/Continuous%20Integration/badge.svg?branch=master)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

Team Metrics Visualizer is a tool teams can use to gather data from various other tools and create helpful visualisations from it.

## Getting started

### Requirements

* Python 3
* Pipenv
* Docker
* npm

### 🖥 Development environment setup

_Note_: All paths given here are relative to the project root.

After cloning the repo, perform the following steps to create your development environment:

1. Install dependencies: ``pipenv sync --dev --python /path/to/your/python3.8``.
1. Install pre-commit hooks: ``pipenv run pre-commit install``.
1. Create ``.env``-file in folder ``tmv`` for configuration. You can find a ``sample.env`` with all required configuration variables in the project root.
1. Switch to folder ``tmv-docker-dev``.
1. Start database container for local development: ``./run_docker-compose.sh``.
1. Switch to custom dash components folder ``tmv_dash_components``.
1. Install dependencies: ``npm i``.
1. Build custom components: ``pipenv run npm run build``.
1. Switch back to app folder ``tmv``.
1. Initialize database: ``pipenv run flask db upgrade head``.

### 🚀 Launch for local development

1. Start database container by executing ``./run_docker-compose.sh`` in folder ``tmv-docker-dev``
1. Start celery: ``pipenv run celery -A runcelery:celery worker -B --loglevel=info``. If you have trouble with this, check the FAQs in the documentation.
1. Start app: ``pipenv run flask run``.

App is reachable at <http://127.0.0.1:8050/>.

If this is the first time you run the app, it is recommended to add yourself as superuser:

1. Add a user: ``pipenv run flask users create --active <your e-mail>``.
1. Add superuser privileges: ``pipenv run flask roles add <your e-mail> superadmin``.

### After pulling a new version

If dependencies were changed (modified `Pipfile`/`Pipfile.lock`), make sure to update
your Python-environment by running `pipenv sync --dev --python /path/to/your/python3.8`.

Always make sure, that your database has the same revision as the ORM. To do so, run this command to upgrade your database to the newest revision: `pipenv run flask db upgrade head`.

### 👩🏻‍💻 Contribution

If you want to contribute to this tool, please have a look at `CONTRIBUTING.md`. 🙂
