#!/bin/bash

set -o errexit
set -o pipefail
set -o nounset

# Check database connection existence
python << END
import sys
import time
import psycopg2

suggest_unrecoverable_after = 30
start = time.time()
while True:
    try:
        conn = psycopg2.connect(
            dbname='${POSTGRES_DB}',
            host='${POSTGRES_HOST}',
            port='${POSTGRES_PORT}',
            user='${POSTGRES_USER}',
            password='${POSTGRES_PASSWORD}'
        )
        conn.close()
        break
    except psycopg2.OperationalError as e:
        if time.time() - start > suggest_unrecoverable_after:
            print('Database connection failed. Exiting...\n')
            sys.stderr.write("Kindly find the causing exception : '{}'".format(e))
            sys.exit(1)
        print('Database connection failed. Retrying...\n')
        time.sleep(1)
END

echo >&2 "Database connection established"
exec "$@"
