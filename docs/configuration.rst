Configuring the .env file
=========================


This application reads most of its required configuration from a ``.env`` file. In it 
are ``key=value`` pairs of variables.
This page aims to explain these variables in greater detail. When creating your ``.env``-file, you
can take the provided ``sample.env`` in folder ``docs`` as an example.

+----------------------------+--------------------------------------------------------------------------------------------------------+------------------------------------------------------------------------------------------------------------------------------+
|          Variable          |                                           Description (dev)                                            |                                                      Description (prod)                                                      |
+============================+========================================================================================================+==============================================================================================================================+
| ``TMV_DEV``                | *Required*. `1` or `0`. For enabling development mode.                                                 |                                                                                                                              |
|                            |                                                                                                        |                                                                                                                              |
+----------------------------+--------------------------------------------------------------------------------------------------------+------------------------------------------------------------------------------------------------------------------------------+
| ``FLASK_ENV``              | *Required*. `development` or `production`. Used for building                                           |                                                                                                                              |
|                            | docker containers.                                                                                     |                                                                                                                              |
+----------------------------+--------------------------------------------------------------------------------------------------------+------------------------------------------------------------------------------------------------------------------------------+
| ``FLASK_DEBUG``            | *Required*. `1` or `0` to enable/disable debug mode on the                                             |                                                                                                                              |
|                            | docker Flask app.                                                                                      |                                                                                                                              |
+----------------------------+--------------------------------------------------------------------------------------------------------+------------------------------------------------------------------------------------------------------------------------------+
| ``FLASK_RUN_PORT``         | *Required*. Suggested: `8050`. Port to run the Flask app on                                            |                                                                                                                              |
|                            | inside the docker container.                                                                           |                                                                                                                              |
+----------------------------+--------------------------------------------------------------------------------------------------------+------------------------------------------------------------------------------------------------------------------------------+
| ``FLASK_SECRET_KEY``       | *Required*. Suggested: generate via                                                                    |                                                                                                                              |
|                            | ``python3 -c "import secrets; print(secrets.token_urlsafe())"``.                                       |                                                                                                                              |
|                            | App secret key.                                                                                        |                                                                                                                              |
+----------------------------+--------------------------------------------------------------------------------------------------------+------------------------------------------------------------------------------------------------------------------------------+
| ``SECURITY_PASSWORD_SALT`` | *Required*. Suggested: generate via                                                                    |                                                                                                                              |
|                            | ``python3 -c "import secrets; print(secrets.token_urlsafe())"``                                        |                                                                                                                              |
|                            | Key used for salting passwords.                                                                        |                                                                                                                              |
+----------------------------+--------------------------------------------------------------------------------------------------------+------------------------------------------------------------------------------------------------------------------------------+
| ``TEMP_UPLOADS_FOLDER``    | *Required*. Suggested: ``./temp_uploads/``. Folder where uploaded files like imported data are stored. |                                                                                                                              |
|                            |                                                                                                        |                                                                                                                              |
+----------------------------+--------------------------------------------------------------------------------------------------------+------------------------------------------------------------------------------------------------------------------------------+
| ``POSTGRES_HOST``          | *Required*. Suggested: ``127.0.0.1``. Host where psql is running.                                      | Required: ``db`` as defined in                                                                                               |
|                            |                                                                                                        | the docker-compose file.                                                                                                     |
+----------------------------+--------------------------------------------------------------------------------------------------------+------------------------------------------------------------------------------------------------------------------------------+
| ``POSTGRES_PORT``          | *Required*. Suggested: ``37432``. Port where psql is reachable.                                        | Required: ``5432`` as defined in                                                                                             |
|                            |                                                                                                        | the docker-compose file.                                                                                                     |
+----------------------------+--------------------------------------------------------------------------------------------------------+------------------------------------------------------------------------------------------------------------------------------+
| ``POSTGRES_USER``          | *Required*. Suggested: ``postgresql``. Psql username.                                                  |                                                                                                                              |
+----------------------------+--------------------------------------------------------------------------------------------------------+------------------------------------------------------------------------------------------------------------------------------+
| ``POSTGRES_PASSWORD``      | *Required*. Suggested: generate via                                                                    |                                                                                                                              |
|                            | ``python3 -c "import secrets; print(secrets.token_urlsafe(16))"``                                      |                                                                                                                              |
|                            | Psql password.                                                                                         |                                                                                                                              |
+----------------------------+--------------------------------------------------------------------------------------------------------+------------------------------------------------------------------------------------------------------------------------------+
| ``POSTGRES_DB``            | *Required*. Suggested: ``tmv``. Name of the database to be used.                                       |                                                                                                                              |
+----------------------------+--------------------------------------------------------------------------------------------------------+------------------------------------------------------------------------------------------------------------------------------+
| ``RABBITMQ_HOST``          | *Required*. Suggested: ``127.0.0.1``. Host where rabbitmq                                              |                                                                                                                              |
|                            | is running.                                                                                            |                                                                                                                              |
+----------------------------+--------------------------------------------------------------------------------------------------------+------------------------------------------------------------------------------------------------------------------------------+
| ``RABBITMQ_PORT``          | *Required*. Suggested: ``37672``. Port where rabbitmq                                                  |                                                                                                                              |
|                            | is reachable.                                                                                          |                                                                                                                              |
+----------------------------+--------------------------------------------------------------------------------------------------------+------------------------------------------------------------------------------------------------------------------------------+
| ``RABBITMQ_ERLANG_COOKIE`` | *Required*. Suggested: generate via                                                                    |                                                                                                                              |
|                            | ``python3 -c "import secrets; print(secrets.token_urlsafe(16))"``                                      |                                                                                                                              |
|                            | Secret used by rabbitmq for communicating between nodes.                                               |                                                                                                                              |
+----------------------------+--------------------------------------------------------------------------------------------------------+------------------------------------------------------------------------------------------------------------------------------+
| ``RABBITMQ_DEFAULT_USER``  | *Required*. Suggested: ``rabbitmq``. Rabbitmq username.                                                |                                                                                                                              |
+----------------------------+--------------------------------------------------------------------------------------------------------+------------------------------------------------------------------------------------------------------------------------------+
| ``RABBITMQ_DEFAULT_PASS``  | *Required*. Suggested: generate via                                                                    |                                                                                                                              |
|                            | ``python3 -c "import secrets; print(secrets.token_urlsafe(16))"``                                      |                                                                                                                              |
|                            | Rabbitmq password.                                                                                     |                                                                                                                              |
+----------------------------+--------------------------------------------------------------------------------------------------------+------------------------------------------------------------------------------------------------------------------------------+
| ``GUNICORN_WORKERS``       | *Not required*, as dev environment serves flask using non-production WSGI.                             | *Required*. Suggested heuristic is ``(2 * num_cores) +1``.                                                                   |
|                            |                                                                                                        | Refer to the `Gunicorn-docs <gunicorn_workers_>`_ and the documentation on `standalone WSGI containers <flask_prod_wsgi_>`_. |
+----------------------------+--------------------------------------------------------------------------------------------------------+------------------------------------------------------------------------------------------------------------------------------+

Integrations
------------

TMV can be used as-is. In doing so, data for the dashboards must be uploaded or entered manually. 
Alternatively, we have integrations to help ease the process. The number of integrations supported is planned to be increased.

Some integrations need configuration in the ``.env``-file. This is optional and 
described in the following.

Okta Oauth/OpenID
#################

TMV supports authentication via Okta. To use, configure `Login redirect URIs` to be `https://yourhost/okta-callback`.

+------------------------+------------------------------------------------------------------+
|        Variable        |                           Description                            |
+========================+==================================================================+
| ``OKTA_ORG_BASEURL``   | *Required if Okta enabled*. Format: ``https://yourorg.okta.com`` |
+------------------------+------------------------------------------------------------------+
| ``OKTA_CLIENT_ID``     | *Required if Okta enabled*. Sourced during setup of okta         |
|                        | callback.                                                        |
+------------------------+------------------------------------------------------------------+
| ``OKTA_CLIENT_SECRET`` | *Required if Okta enabled*. Sourced during setup of okta         |
|                        | callback.                                                        |
+------------------------+------------------------------------------------------------------+

JIRA
####

For dashboards relating to Sprint data such as `Burnup` and `Cumulative Flow`, integration with JIRA is supported.

To integrate, an application link must be created on JIRA. An RSA file may be needed which can be generated using the following commands:

.. code-block::

   openssl genrsa -out rsa.pem 2048
   openssl rsa -in rsa.pem -pubout -out rsa.pub

Afterwards, an OAuth dance must be done to get the `JIRA_ACCESS_TOKEN` and `JIRA_ACCESS_SEC` variables. This OAuth dance only needs to be done once and can be done so using the following command:

.. code-block::

   jirashell --server https://yourorg.atlassian.net.com --consumer-key tmv-key --key-cert rsa.pem --oauth-dance

After approving the access in the browser popup, a python shell will appear. The OAuth details can be accessed by issuing the command ``oauth``:

+----------------------------+--------------------------------------------------------------------------------------+
|          Variable          |                                     Description                                      |
+============================+======================================================================================+
| ``JIRA_SERVER``            | *Required if JIRA enabled*. Format:                                                  |
|                            | ``https://yourorg.atlassian.net`` or your on-prem URL.                               |
|                            | JIRA server to connect to. Currently, both JIRA Server and JIRA Cloud are supported. |
+----------------------------+--------------------------------------------------------------------------------------+
| ``JIRA_CONSUMER_KEY``      | *Required if JIRA enabled*. User-supplied key as setup on                            |
|                            | JIRA.                                                                                |
+----------------------------+--------------------------------------------------------------------------------------+
| ``JIRA_CONSUMER_SECRET``   | *Not needed yet*. Not yet needed as we don't yet have any push events                |
|                            | to JIRA.                                                                             |
+----------------------------+--------------------------------------------------------------------------------------+
| ``JIRA_OAUTH_LOC``         | *Required if JIRA enabled*. ``AWS`` or ``ENV``. If ``ENV``, the                      |
|                            | next three variables are also required. If ``AWS``, the next                         |
|                            | three variables must be set on                                                       |
|                            | `AWS Secrets Manager <aws_tutorial_>`_.                                              |
+----------------------------+--------------------------------------------------------------------------------------+
| ``JIRA_ACCESS_TOKEN``      | *Required* if ``JIRA_OAUTH_LOC`` is ``ENV``. See above for                           |
|                            | instructions.                                                                        |
+----------------------------+--------------------------------------------------------------------------------------+
| ``JIRA_ACCESS_SEC``        | *Required* if ``JIRA_OAUTH_LOC`` is ``ENV``. See above for                           |
|                            | instructions.                                                                        |
+----------------------------+--------------------------------------------------------------------------------------+
| ``JIRA_RSA_PEM``           | *Required* if ``JIRA_OAUTH_LOC`` is ``ENV``. Format: |rsa_format|.                   |
|                            | The contents of the RSA private key in a single line. See                            |
|                            | above for instructions on hot to generate this.                                      |
+----------------------------+--------------------------------------------------------------------------------------+
| ``JIRA_FIELD_SPRINT``      | *Required if JIRA enabled*. Suggested: ``Sprint``. The name of                       |
|                            | the Sprint field in your JIRA projects.                                              |
+----------------------------+--------------------------------------------------------------------------------------+
| ``JIRA_FIELD_STORYPOINTS`` | *Required if JIRA enabled*. Suggested: ``Story Points``. The                         |
|                            | name of the JIRA Story Points field in your projects.                                |
+----------------------------+--------------------------------------------------------------------------------------+

.. _aws_tutorial: https://docs.aws.amazon.com/secretsmanager/latest/userguide/tutorials_basic.html
.. |rsa_format| replace:: ``-----BEGIN RSA PRIVATE KEY----- key_here_all_in_one_line -----END RSA PRIVATE KEY-----``
.. _gunicorn_workers: https://docs.gunicorn.org/en/stable/design.html#how-many-workers
.. _flask_prod_wsgi: https://flask.palletsprojects.com/en/1.1.x/deploying/wsgi-standalone/