#!/bin/sh

set -eu

SCRIPT_DIRECTORY=${UPW_POSTGRES_SCRIPT_DIRECTORY:-/opt/upw/postgres}
. "$SCRIPT_DIRECTORY/common.sh"

for variable_name in POSTGRES_DB POSTGRES_AUDIT_OPERATOR_USER POSTGRES_AUDIT_OPERATOR_PASSWORD PGHOST
do
    require_environment "$variable_name"
done
validate_identifier POSTGRES_DB
validate_identifier POSTGRES_AUDIT_OPERATOR_USER
validate_url_safe_secret POSTGRES_AUDIT_OPERATOR_PASSWORD

PGDATABASE=$POSTGRES_DB
PGUSER=$POSTGRES_AUDIT_OPERATOR_USER
PGPASSWORD=$POSTGRES_AUDIT_OPERATOR_PASSWORD
export PGDATABASE PGUSER PGPASSWORD
run_psql_file "$SCRIPT_DIRECTORY/check-audit-permissions.sql"
printf '%s\n' "PostgreSQL audit-retention operator permissions are verified."
