#!/bin/sh

set -eu

umask 077

require_environment() {
    variable_name=$1
    eval "variable_value=\${$variable_name-}"
    if [ -z "$variable_value" ]; then
        printf '%s\n' "Required PostgreSQL role configuration is missing: $variable_name" >&2
        exit 2
    fi
}

validate_identifier() {
    variable_name=$1
    eval "identifier=\${$variable_name-}"
    case "$identifier" in
        ''|[0-9]*|*[!A-Za-z0-9_]*)
            printf '%s\n' "$variable_name must be an ASCII PostgreSQL identifier." >&2
            exit 2
            ;;
    esac
    if [ "${#identifier}" -gt 63 ]; then
        printf '%s\n' "$variable_name must not exceed 63 ASCII characters." >&2
        exit 2
    fi
}

validate_url_safe_secret() {
    variable_name=$1
    eval "secret_value=\${$variable_name-}"
    case "$secret_value" in
        ''|*[!A-Za-z0-9._~-]*)
            printf '%s\n' "$variable_name must be a non-empty URL-safe secret." >&2
            exit 2
            ;;
    esac
    if [ "${#secret_value}" -lt 32 ]; then
        printf '%s\n' "$variable_name must contain at least 32 characters." >&2
        exit 2
    fi
}

require_distinct_roles() {
    if [ "$POSTGRES_USER" = "$POSTGRES_MIGRATION_USER" ] || \
       [ "$POSTGRES_USER" = "$POSTGRES_RUNTIME_USER" ] || \
       [ "$POSTGRES_USER" = "$POSTGRES_AUDIT_OPERATOR_USER" ] || \
       [ "$POSTGRES_MIGRATION_USER" = "$POSTGRES_RUNTIME_USER" ] || \
       [ "$POSTGRES_MIGRATION_USER" = "$POSTGRES_AUDIT_OPERATOR_USER" ] || \
       [ "$POSTGRES_RUNTIME_USER" = "$POSTGRES_AUDIT_OPERATOR_USER" ]; then
        printf '%s\n' "Bootstrap, migration, runtime, and audit-operator PostgreSQL roles must be distinct." >&2
        exit 2
    fi
}

require_distinct_passwords() {
    if [ "$POSTGRES_PASSWORD" = "$POSTGRES_MIGRATION_PASSWORD" ] || \
       [ "$POSTGRES_PASSWORD" = "$POSTGRES_RUNTIME_PASSWORD" ] || \
       [ "$POSTGRES_PASSWORD" = "$POSTGRES_AUDIT_OPERATOR_PASSWORD" ] || \
       [ "$POSTGRES_MIGRATION_PASSWORD" = "$POSTGRES_RUNTIME_PASSWORD" ] || \
       [ "$POSTGRES_MIGRATION_PASSWORD" = "$POSTGRES_AUDIT_OPERATOR_PASSWORD" ] || \
       [ "$POSTGRES_RUNTIME_PASSWORD" = "$POSTGRES_AUDIT_OPERATOR_PASSWORD" ]; then
        printf '%s\n' "Bootstrap, migration, runtime, and audit-operator PostgreSQL passwords must be distinct." >&2
        exit 2
    fi
}

run_psql_file() {
    sql_file=$1
    psql \
        --no-psqlrc \
        --set=ON_ERROR_STOP=1 \
        --file="$sql_file"
}
