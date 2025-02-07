#!/usr/bin/env bash

set -o errexit
set -o pipefail
set -o nounset

working_dir="$(dirname ${0})"
source "${working_dir}/_sourced/constants.sh"
source "${working_dir}/_sourced/messages.sh"

message_welcome "Backing up the '${POSTGRES_DB}' database..."

# if [[ "${POSTGRES_USER}" == "postgres" ]]; then
#     message_error "Backing up as postgres user is not allowed. Assign 'POSTGRES_USER' env to 
#     another user and try again."
#     exit 1
# fi

export PGHOST="${POSTGRES_HOST}"
export PGPORT="${POSTGRES_PORT}"
export PGDATABASE="${POSTGRES_DB}"
export PGUSER="${POSTGRES_USER}"
export PGPASSWORD="${POSTGRES_PASSWORD}"

backup_filename="${BACKUP_FILE_PREFIX}_$(date +'%Y_%m_%dT%H_%M_%S').sql.gz"

if ! pg_dump | gzip > "${BACKUP_DIR_PATH}/${backup_filename}"; then
    message_error "Failed to backup the '${POSTGRES_DB}' database. Please check the postgres logs 
    for more information."
    exit 1
fi

message_success "Backup of '${POSTGRES_DB}' database completed successfully. Backup file: 
    '${backup_filename}' is in the backup directory '${BACKUP_DIR_PATH}'"
