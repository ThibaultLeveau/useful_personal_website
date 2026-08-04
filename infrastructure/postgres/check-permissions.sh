#!/bin/sh

set -eu

SCRIPT_DIRECTORY=${UPW_POSTGRES_SCRIPT_DIRECTORY:-/opt/upw/postgres}
. "$SCRIPT_DIRECTORY/common.sh"

for variable_name in \
    POSTGRES_DB \
    POSTGRES_MIGRATION_USER \
    POSTGRES_RUNTIME_USER \
    PGHOST \
    PGUSER \
    PGPASSWORD
do
    require_environment "$variable_name"
done

validate_identifier POSTGRES_DB
validate_identifier POSTGRES_MIGRATION_USER
validate_identifier POSTGRES_RUNTIME_USER

if [ "$PGUSER" != "$POSTGRES_RUNTIME_USER" ]; then
    printf '%s\n' "Permission verification must connect as the runtime role." >&2
    exit 2
fi

run_psql_file "$SCRIPT_DIRECTORY/check-permissions.sql"
printf '%s\n' "PostgreSQL runtime permission gate passed."
