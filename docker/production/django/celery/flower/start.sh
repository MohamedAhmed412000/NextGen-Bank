#!/bin/bash

set -o errexit
set -o nounset

worker_ready() {
	celery -A config.celery_app inspect ping
}

until worker_ready; do
	echo >&2 "Waiting for celery workers to start..."
	sleep 1
done

echo >&2 "Celery workers started"

exec celery \
	-A config.celery_app \
	-b "${CELERY_BROKER_URL}" \
	flower \
	--basic_auth="${CELERY_FLOWER_USER}:${CELERY_FLOWER_PASSWORD}"
 