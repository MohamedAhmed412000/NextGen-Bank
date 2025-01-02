FROM docker.io/python:3.9.5-slim-buster AS python

# Stage 1: Install dependencies
FROM python AS python-build-stage

ARG BUILD_ENVIRONMENT=local

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev

COPY ./requirements .

RUN pip wheel --wheel-dir /usr/src/app/wheels -r ${BUILD_ENVIRONMENT}.txt

# Stage 2: Run Stage
FROM python AS python-run-stage

ARG BUILD_ENVIRONMENT=local

ARG APP_HOME=/app

ENV PYTHONDONTWRITEBYTECODE 1 \
    PYTHONUNBUFFERED 1 \
    BUILD_ENV=${BUILD_ENVIRONMENT}

WORKDIR ${APP_HOME}

RUN apt-get update && apt-get install -y --no-install-recommends \
    sudo git bash-completion nano ssh libpq-dev gettext \
    && apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false \
    && rm -rf /var/lib/apt/lists/*

RUN addgroup --system django && \ 
    adduser --system --ingroup django django && \
    mkdir -p ${APP_HOME}/staticfiles && \
    chown django:django ${APP_HOME}/staticfiles && \
    chmod 775 ${APP_HOME}/staticfiles

COPY --from=python-build-stage /usr/src/app/wheels /wheels

RUN pip install --no-cache-dir --no-index --find-links=/wheels /wheels/* \
    && rm -rf /wheels

COPY --chown=django:django ./docker/local/django/entrypoint.sh /entrypoint.sh
COPY --chown=django:django ./docker/local/django/start.sh /start.sh
COPY --chown=django:django ./docker/local/django/celery/worker/start.sh /start-celeryworker.sh
COPY --chown=django:django ./docker/local/django/celery/beat/start.sh /start-celerybeat.sh
COPY --chown=django:django ./docker/local/django/celery/flower/start.sh /start-flower.sh

RUN sed -i 's/\r$//g' /entrypoint.sh /start.sh /start-celeryworker.sh /start-celerybeat.sh /start-flower.sh && \
    chmod +x /entrypoint.sh /start.sh /start-celeryworker.sh /start-celerybeat.sh /start-flower.sh

COPY --chown=django:django . ${APP_HOME}

USER django

ENTRYPOINT ["/entrypoint.sh"]
