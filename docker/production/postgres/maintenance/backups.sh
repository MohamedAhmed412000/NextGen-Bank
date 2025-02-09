#!/usr/bin/env bash

set -o errexit
set -o pipefail
set -o nounset

working_dir="$(dirname ${0})"
source "${working_dir}/_sourced/constants.sh"
source "${working_dir}/_sourced/messages.sh"

message_welcome "These are the backups that you have created so far:"

echo "Timestamp               Size     Filename"
echo "---------------------   -----    --------"
ls -lht "${BACKUP_DIR_PATH}" | awk 'NR>1 {printf "%-21s %-7s %s\n", $6" "$7" "$8, $5, $9}'
