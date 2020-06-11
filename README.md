# swp-scrum-tmv
Team Metrics Visualizer is a tool to gather data on teams from various sources and visualize the results in dashboards.

## Getting started
### Requirements
* Python3
* Pipenv
* Docker

Relative paths in this README are to be understood relative to the repository directory.

### First setup
1. Install python dependencies: `pipenv sync --dev --python=python3`
1. Install pre-commit hooks. This will run linter on commit: `pipenv run pre-commit install`
1. Switch to app folder: `cd tmv` (this is the folder containing `app.py`)
1. Copy sample env file: `cp ../sample.env .env`
1. Change the values in `.env`
1. Switch to docker dev folder: `cd ../tmv-docker-dev/`
1. Start database container: `./run_docker-compose.sh`
1. Switch to custom dash components folder: `cd ../tmv_dash_components/`
1. Install dependencies: `npm i`
1. Build custom components: `pipenv run npm run build`
1. Switch back to app folder: `cd ../tmv/`
1. Initialize database: `pipenv run flask db upgrade head`

### Run/launch
1. Start database container by executing `./run_docker-compose.sh` in folder `tmv-docker-dev`.
1. Run celery worker: `pipenv run celery -A runcelery:celery worker -B --loglevel=info`.
1. Start app: `pipenv run flask run`. 

App is reachable at `http://127.0.0.1:8050/dash/`.

## Migrations
We use [Flask-Migrate](https://flask-migrate.readthedocs.io/en/latest/) to create data migrations that apply data-model changes. Flask-Migrate helps you make sure that the code (the ORM actually) is aligned with the data you have on your DB.

### You have made changes to the data model
If you make changes to the data model, editing or creating tables or fields, make sure that you create a migration and apply it to the DB. Generated migration files should be checked because not all changes are caught by Flask-Migrate.
```
# Create the migration file
flask db migrate -m "Optional migration message. It could be something like ``Added name field``"
# Apply the migration
flask db upgrade
```

### You have pulled new code
Every time you run new code, you have to make sure your DB has the same revision as the ORM. To do so, run the command to upgrade your DB to the ORM's revision: `flask db upgrade head`

### Other useful commands
- Show a list of revisions with `flask db history`
- Revert to previous revision with `flask db downgrade`
- Show the current DB revision with `flask db current`
- Add a user: `flask users create --active [email]`
- Add a role to a user: `flask roles add [email] [role: superadmin, dataprovider]`

## Theming
We use [Dash Bootstrap Components](https://dash-bootstrap-components.opensource.faculty.ai/) for most UI components.
We use [Bootstrap](https://getbootstrap.com/) with Sass to style them.
If you want to customize the style, edit the SCSS files at `tmv/style` and generate the CSS:
1. From the main project folder: `npm install` and `npm run build`.
2. Webpack will generate `main.css` and `main.js` files in `./tmv/static/dash` folder.

## Jira Setup
If Jira is setup and you navigate to the `{server}/admin/activity/` admin page, JiraProjects will be loaded which can be assigned to Activities.

### Status to Status Category Mappings

For the Sprint-related charts to work properly, mappings must be configured. If Jira is setup, `{server}/admin/statuscategorystatusmapping/` has a button to load the default mappings from Jira. The default mappings show Activity as not set in the admin page. To create activity-specific mappings, just create the mappings with Activity set to that specific activity. These will take priority over the default mappings.

During the generation of default mappings, there's a chance that not all statuses will be mapped. A message will be flashed at the top of the page if so. This info is also available at the console logs.

Also, it's possible to override the default mappings by setting the Status Category to something else. These changes will persist even if you load the default values from Jira again. If you want to reset the mappings, delete all the rows with Activity as not set then load the Jira mappings again.

## Remarks
You can exit the container like this:
1. Press `ctrl+P`, then `ctrl+Q`
1. Now you left the container and are in the folder you were before.
You can get back in like this:
1. `docker ps`
1. Copy `CONTAINER ID` of container `tmv`
1. Execute `docker exec -it <CONTAINER ID> /bin/bash`
1. Now you are back in the container.

## FAQs
1. I have encountered the error `FATAL:  password authentication failed for user "postgres"`

   Environmental variable in Docker are loaded when containers are built (with `docker-compose up -d`). If you added or changed variables in `.env` after the containers were built, then you need to recreate the containers (with `./run_docker-compose.sh`) to load the updated values. You won't lose data unless you explicitly delete the `tmv_db` volume.

2. I have encountered the error `billiard.exceptions.WorkerLostError: Worker exited prematurely: signal 6 (SIGABRT)` while trying to run Celery

   You need to set the following environment variable in your `.bash_profile`: `OBJC_DISABLE_INITIALIZE_FORK_SAFETY=YES`. For more info, check this [stackoverflow answer](https://stackoverflow.com/questions/52671926/rails-may-have-been-in-progress-in-another-thread-when-fork-was-called).

   For some users MacOSX, the fix above is not enough. In that case, try attaching `--pool=solo` to the celery command:

   `pipenv run celery -A runcelery:celery worker -B --loglevel=info --pool=solo`

