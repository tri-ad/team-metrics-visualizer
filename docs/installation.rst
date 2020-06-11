Installation
============

Requirements
------------
+ Python 3.8
+ Pipenv
+ Docker
+ npm

Development environment setup
-----------------------------
*Note*: All paths given here are relative to the project root.

After cloning the repo, perform the following steps to create your development environment:

#. Install dependencies: ``pipenv sync --dev --python /path/to/your/python3.8``.
#. Install pre-commit hooks: ``pipenv run pre-commit install``.
#. Create ``.env``-file in folder ``tmv`` for configuration. You can find a ``sample.env`` with all required configuration variables in the project root.
#. Switch to folder ``tmv-docker-dev``.
#. Start database container for local development: ``./run_docker-compose.sh``.
#. Switch to custom dash components folder ``tmv_dash_components``.
#. Install dependencies: ``npm i``.
#. Build custom components: ``pipenv run npm run build``.
#. Switch back to app folder ``tmv``.
#. Initialize database: ``pipenv run flask db upgrade head``.

Launch for local development
----------------------------

#. Start database container by executing ``./run_docker-compose.sh`` in folder ``tmv-docker-dev``
#. Run celery worker: ``pipenv run celery -A runcelery:celery worker -B --loglevel=info``. If you have trouble with this, check the :doc:`faqs`.
#. Start app: ``pipenv run flask run``. 

App is reachable at http://127.0.0.1:8050/.

If this is the first time you run the app, it is recommended to add yourself as superuser:

#. Add a user: ``pipenv run flask users create --active <your e-mail>``.
#. Add superuser privileges: ``pipenv run flask roles add <your e-mail> superadmin``.

After pulling a new version
---------------------------

If dependencies were changed (modified `Pipfile`/`Pipfile.lock`), make sure to update
your Python-environment by running ``pipenv sync --dev --python /path/to/your/python3.8``.

Always make sure, that your database has the same revision as the ORM. To do so, run this 
command to upgrade your database to the newest revision: ``pipenv run flask db upgrade head``.