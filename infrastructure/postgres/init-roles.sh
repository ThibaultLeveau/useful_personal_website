#!/bin/sh

set -eu

SCRIPT_DIRECTORY=${UPW_POSTGRES_SCRIPT_DIRECTORY:-/opt/upw/postgres}
. "$SCRIPT_DIRECTORY/common.sh"

for variable_name in \
    POSTGRES_DB \
    POSTGRES_USER \
    POSTGRES_PASSWORD \
    POSTGRES_MIGRATION_USER \
    POSTGRES_MIGRATION_PASSWORD \
    POSTGRES_RUNTIME_USER \
    POSTGRES_RUNTIME_PASSWORD \
    POSTGRES_AUDIT_OPERATOR_USER \
    POSTGRES_AUDIT_OPERATOR_PASSWORD
do
    require_environment "$variable_name"
done

validate_identifier POSTGRES_DB
validate_identifier POSTGRES_USER
validate_identifier POSTGRES_MIGRATION_USER
validate_identifier POSTGRES_RUNTIME_USER
validate_identifier POSTGRES_AUDIT_OPERATOR_USER
validate_url_safe_secret POSTGRES_PASSWORD
validate_url_safe_secret POSTGRES_MIGRATION_PASSWORD
validate_url_safe_secret POSTGRES_RUNTIME_PASSWORD
validate_url_safe_secret POSTGRES_AUDIT_OPERATOR_PASSWORD
require_distinct_roles
require_distinct_passwords

if [ -z "${PGDATABASE-}" ]; then
    PGDATABASE=$POSTGRES_DB
    export PGDATABASE
fi
if [ -z "${PGUSER-}" ]; then
    PGUSER=$POSTGRES_USER
    export PGUSER
fi
if [ -z "${PGPASSWORD-}" ]; then
    PGPASSWORD=$POSTGRES_PASSWORD
    export PGPASSWORD
fi

run_psql_file "$SCRIPT_DIRECTORY/init-roles.sql"
printf '%s\n' "PostgreSQL migration-owner and runtime roles are reconciled."
