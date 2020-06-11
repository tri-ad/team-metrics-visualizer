# Deployment

Requirements: `docker` and `docker-compose`

1. Clone the repo and open `tmv-docker-prod` folder
2. Copy sample env file and update values: `cp ../sample.env .env`
3. [Expose app container's port](#exposing-apps-port) or use [nginx reverse proxy docker companion](#https-via-lets-encrypt)
4. Build images: `./docker-compose.sh build --pull`
5. Start containers: `./docker-compose.sh up -d`

## Exposing app's port

By default, app container's port is not exposed. If you don't need [https](#https-via-lets-encrypt), you can open port directly

1. Add `-f docker-compose_tmv_open_port.yml` to `default_docker_compose_args`
2. Add `TMV_OPEN_PORT` env var to `.env` file. E.g. `TMV_OPEN_PORT=8050`

## https via Let's Encrypt

If you don't already have a running web server on the host, you can use [docker-compose-letsencrypt-nginx-proxy-companion](https://github.com/evertramos/docker-compose-letsencrypt-nginx-proxy-companion) to run nginx reverse proxy to the app and enable https via Let's Encrypt

1. Create `docker-compose_proxy.yml` file:
```docker-compose.yml
version: "3"

services:
  tmv:
    environment:
      - VIRTUAL_PORT=8000  # app container's port, don't change
      - VIRTUAL_HOST=example.com  # your domain
      - LETSENCRYPT_HOST=example.com  # to enable https (optional)
      - LETSENCRYPT_EMAIL=admin@example.com
    networks:
      - proxy

networks:
  proxy:
    external:
      name: ${NETWORK:-webproxy}
```
2. Add `-f docker-compose_proxy.yml` to `default_docker_compose_args`
3. Restart containers

## Using external database

In case you want to use an external database, you can remove `-f docker-compose_db.yml` from `default_docker_compose_args` and point `.env` file vars to an external PostgreSQL.

## Files

### `docker-compose.sh` and `default_docker_compose_args`

`default_docker_compose_args` file contains `docker-compose` args that are automatically included if you use `docker-compose.sh` script. For example if it contains `-f docker-compose_base.yml -f docker-compose_db.yml`, running `./docker-compose.sh up -d` would translate to `docker-compose -f docker-compose_base.yml -f docker-compose_db.yml up -d`
