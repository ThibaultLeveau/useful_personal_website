#!/bin/sh

set -eu

SCRIPT_DIRECTORY=${UPW_POSTGRES_SCRIPT_DIRECTORY:-/opt/upw/postgres}
. "$SCRIPT_DIRECTORY/common.sh"

for variable_name in \
    POSTGRES_DB \
    POSTGRES_MIGRATION_USER \
    POSTGRES_RUNTIME_USER \
    POSTGRES_RUNTIME_PASSWORD \
    POSTGRES_AUDIT_OPERATOR_USER \
    POSTGRES_AUDIT_OPERATOR_PASSWORD \
    PGHOST \
    PGUSER \
    PGPASSWORD
do
    require_environment "$variable_name"
done

validate_identifier POSTGRES_DB
validate_identifier POSTGRES_MIGRATION_USER
validate_identifier POSTGRES_RUNTIME_USER
validate_identifier POSTGRES_AUDIT_OPERATOR_USER
validate_url_safe_secret POSTGRES_RUNTIME_PASSWORD
validate_url_safe_secret POSTGRES_AUDIT_OPERATOR_PASSWORD

if [ "$PGUSER" != "$POSTGRES_MIGRATION_USER" ]; then
    printf '%s\n' "Permission reconciliation must connect as the migration owner." >&2
    exit 2
fi

run_psql_file "$SCRIPT_DIRECTORY/reconcile-permissions.sql"

PGUSER=$POSTGRES_RUNTIME_USER
PGPASSWORD=$POSTGRES_RUNTIME_PASSWORD
export PGUSER PGPASSWORD
sh "$SCRIPT_DIRECTORY/check-permissions.sh"
sh "$SCRIPT_DIRECTORY/check-audit-permissions.sh"
printf '%s\n' "PostgreSQL runtime permissions are reconciled and verified."
