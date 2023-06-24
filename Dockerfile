########################################
# Base image
########################################

FROM python:3.9-slim AS base
SHELL ["/bin/bash", "-c"]
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
WORKDIR /service
USER root

RUN apt-get update
RUN apt-get install -y --no-install-recommends git build-essential

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements*.txt ./
RUN pip3 install -r requirements-prod.txt

########################################
# Release image
########################################

FROM python:3.9-slim
SHELL ["/bin/bash", "-c"]
ENV PYTHONUNBUFFERED=1
WORKDIR /service

ARG ENVIRONMENT=prod
ARG SERVICE_NAME=pool-manager-stub
ARG SERVICE_VERSION=None
ARG COMMIT_ID=None
ARG COMMIT_DATE=None
ARG BUILD_DATE=None
ARG GIT_BRANCH=None

ENV ENVIRONMENT=$ENVIRONMENT
ENV SERVICE_NAME=$SERVICE_NAME
ENV SERVICE_VERSION=$SERVICE_VERSION
ENV COMMIT_ID=$COMMIT_ID
ENV COMMIT_DATE=$COMMIT_DATE
ENV BUILD_DATE=$BUILD_DATE
ENV GIT_BRANCH=$GIT_BRANCH

COPY --from=base /opt/venv /opt/venv
COPY logging.yaml index.html ./
COPY pool_manager ./pool_manager

ENV PATH="/opt/venv/bin:$PATH"
CMD python3 -O -m uvicorn \
	--factory pool_manager.app.main:create_app \
    --host 0.0.0.0 \
    --port 8080 \
    --workers 1 \
    --log-config logging.yaml \
    --lifespan on
