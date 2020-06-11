FROM ubuntu:latest

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && \
    apt-get install nodejs npm python3 python3-pip -y && \
    node --version && \
    python3 --version && \
    python3 -m pip install "dash[dev]>=1.3.1"

COPY ./tmv_dash_components/package.json /src/tmv_dash_components/
COPY ./tmv_dash_components/package-lock.json /src/tmv_dash_components/
WORKDIR /src/tmv_dash_components/
RUN npm i

COPY ./tmv_dash_components/ /src/tmv_dash_components/
COPY ./tmv/style/ /src/tmv/style/

RUN npm run build:js && npm run build:py

FROM python:3.8-slim

# TODO: pipenv's --system is broken in new versions, update when fixed
# https://github.com/pypa/pipenv/issues/4311
# https://github.com/pypa/pipenv/pull/4319
RUN pip install -U pip pipenv==2018.11.26

COPY ./Pipfile /src/
COPY ./Pipfile.lock /src/

WORKDIR /src

RUN pipenv install --system --sequential

COPY --from=0 /src/tmv_dash_components/tmv_dash_components/ \
              /src/tmv_dash_components/tmv_dash_components/
