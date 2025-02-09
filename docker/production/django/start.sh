#!/bin/bash

set -o errexit
set -o pipefail
set -o nounset

python /app/manage.py migrate --no-input
python /app/manage.py collectstatic --no-input

NUM_WORKERS=${GUNICORN_WORKERS:-3}
exec /usr/local/bin/gunicorn config.wsgi --bind 0.0.0.0:8000 --chdir=/app --workers $NUM_WORKERS
