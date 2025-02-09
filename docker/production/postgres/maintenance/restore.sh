#!/usr/bin/env bash

set -o errexit
set -o pipefail
set -o nounset

working_dir="$(dirname ${0})"
source "${working_dir}/_sourced/constants.sh"
source "${working_dir}/_sourced/messages.sh"
source "${working_dir}/_sourced/yes_no.sh"

if [[ -z ${1+x} ]]; then
    message_error "Backup filename is not specified yet. it's required to restore the backup"
    exit 1
fi

backup_filename="${BACKUP_DIR_PATH}/${1}"
if [[ ! -f "${backup_filename}" ]]; then
    message_error "Backup file not found: ${backup_filename}. Please check the 'backups' script output"
    exit 1
fi

message_welcome "Restoring the '${POSTGRES_DB}' database from the '${backup_filename}' backup..."

# if [[ "${POSTGRES_USER}" == "postgres" ]]; then
#     message_error "Restoring as postgres user is not allowed. Assign 'POSTGRES_USER' env to 
#     another user and try again."
#     exit 1
# fi

export PGHOST="${POSTGRES_HOST}"
export PGPORT="${POSTGRES_PORT}"
export PGDATABASE="${POSTGRES_DB}"
export PGUSER="${POSTGRES_USER}"
export PGPASSWORD="${POSTGRES_PASSWORD}"

message_info "This will drop the existing database. Are you sure you want to proceed?"
if ! yes_no "Continue with restore"; then
    message_info "Restore cancelled"
    exit 0
fi

message_info "Terminating existing database connections..."

psql -c "SELECT pg_terminate_backend(pg_stat_activity.pid) FROM pg_stat_activity WHERE 
pg_stat_activity.datname = '${POSTGRES_DB}' AND pid <> pg_backend_pid();" postgres
sleep 2

message_info "Dropping the database..."
dropdb "${PGDATABASE}"

message_info "creating new database..."
createdb --owner="${POSTGRES_USER}"

message_info "Restoring the backup to the new database..."
gunzip -c "${backup_filename}" | psql "${PGDATABASE}"

message_success "Database '${PGDATABASE}' restored successfully from backup '${backup_filename}'"
