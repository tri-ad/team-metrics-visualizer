Deployment
==========

Requirements
------------
+ Docker
+ docker-compose

Deployment instructions
-----------------------
On your remote server, do the following:

#.  Clone the repo
#.  Switch to folder ``tmv-docker-prod``.
#.  In ``tmv-docker-prod``, create a file ``.env`` for configuration. You can use the 
    provided ``sample.env`` as a template - it contains all necessary configuration variables.
#.  Either expose the app container's port or use nginx reverse proxy docker companion 
    (see below for instructions).
#.  Build the docker-images: ``./docker-compose.sh build --pull``
#.  Start the containers: ``./docker-compose.sh up -d``

Exposing the app's port
~~~~~~~~~~~~~~~~~~~~~~~
By default, the app-container's port is not exposed. If you don't need https, you can 
open the port directly, like follows:

#.  Add ``-f docker-compose_tmv_open_port.yml`` to the file ``default_docker_compose_args``.
#.  Configure ``TMV_OPEN_PORT`` in ``.env`` file. E.g. ``TMV_OPEN_PORT=8050``.

Another option is to use **https via Let's Encript**:
If you don't already have a running web server on the host, you can use 
`docker-compose-letsencrypt-nginx-proxy-companion`_ to run nginx reverse proxy to the 
app and enable https via Let's Encrypt. It works like this:

#.  Create ``docker-compose_proxy.yml`` file:

    .. code-block:: yaml

        version: "3"

        services:
        tmv:
            environment:
            - VIRTUAL_PORT=8000             # app container's port, don't change this!
            - VIRTUAL_HOST=example.com      # your domain
            - LETSENCRYPT_HOST=example.com  # to enable https (optional)
            - LETSENCRYPT_EMAIL=admin@example.com
            networks:
            - proxy

        networks:
        proxy:
            external:
            name: ${NETWORK:-webproxy}

#.  Add ``-f docker-compose_proxy.yml`` to ``default_docker_compose_args``.
#.  Restart the containers.

.. _`docker-compose-letsencrypt-nginx-proxy-companion`: https://github.com/evertramos/docker-compose-letsencrypt-nginx-proxy-companion

Usage of external database
~~~~~~~~~~~~~~~~~~~~~~~~~~
In case you would rather use an external database, you can remove 
``-f docker-compose_db.yml`` from ``default_docker_compose_args`` and configure the
variables in ``.env`` to point to an external PostgreSQL-database.

On ``docker-compose.sh`` and ``default_docker_compose_args``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
The file ``default_docker_compose_args`` contains ``docker-compose`` arguments that are 
automatically included if you use the ``docker-compose.sh`` script. 

For example if it 
contains ``-f docker-compose.yml -f docker-compose_db.yml``, running 
``./docker-compose.sh up -d`` would translate to:

.. code-block:: shell

    docker-compose -f docker-compose.yml -f docker-compose_db.yml up -d

