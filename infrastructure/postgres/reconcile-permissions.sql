\set ON_ERROR_STOP on
\getenv database_name POSTGRES_DB
\getenv migration_user POSTGRES_MIGRATION_USER
\getenv runtime_user POSTGRES_RUNTIME_USER
\getenv audit_operator_user POSTGRES_AUDIT_OPERATOR_USER

SELECT format('REVOKE ALL PRIVILEGES ON DATABASE %I FROM PUBLIC', :'database_name')
\gexec
SELECT format('REVOKE ALL PRIVILEGES ON DATABASE %I FROM %I', :'database_name', :'runtime_user')
\gexec
SELECT format('GRANT CONNECT ON DATABASE %I TO %I', :'database_name', :'runtime_user')
\gexec
SELECT format('REVOKE ALL PRIVILEGES ON DATABASE %I FROM %I', :'database_name', :'audit_operator_user')
\gexec
SELECT format('GRANT CONNECT ON DATABASE %I TO %I', :'database_name', :'audit_operator_user')
\gexec

REVOKE ALL PRIVILEGES ON SCHEMA public FROM PUBLIC;
SELECT format('REVOKE ALL PRIVILEGES ON SCHEMA public FROM %I', :'runtime_user')
\gexec
SELECT format('GRANT USAGE ON SCHEMA public TO %I', :'runtime_user')
\gexec
SELECT format('REVOKE ALL PRIVILEGES ON SCHEMA public FROM %I', :'audit_operator_user')
\gexec
SELECT format('GRANT USAGE ON SCHEMA public TO %I', :'audit_operator_user')
\gexec

SELECT format('REVOKE ALL PRIVILEGES ON ALL TABLES IN SCHEMA public FROM %I', :'runtime_user')
\gexec
SELECT format(
    'GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO %I',
    :'runtime_user'
)
\gexec
SELECT format('REVOKE ALL PRIVILEGES ON TABLE public.alembic_version FROM %I', :'runtime_user')
\gexec
SELECT format('GRANT SELECT ON TABLE public.alembic_version TO %I', :'runtime_user')
\gexec
SELECT format('REVOKE ALL PRIVILEGES ON TABLE public.audit_entry FROM %I', :'runtime_user')
\gexec
SELECT format('GRANT SELECT, INSERT ON TABLE public.audit_entry TO %I', :'runtime_user')
\gexec
SELECT format('REVOKE ALL PRIVILEGES ON ALL TABLES IN SCHEMA public FROM %I', :'audit_operator_user')
\gexec
SELECT format('GRANT SELECT, INSERT ON TABLE public.audit_entry TO %I', :'audit_operator_user')
\gexec

SELECT format('REVOKE ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public FROM %I', :'runtime_user')
\gexec
SELECT format('GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO %I', :'runtime_user')
\gexec
REVOKE EXECUTE ON ALL FUNCTIONS IN SCHEMA public FROM PUBLIC;
SELECT format('REVOKE ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA public FROM %I', :'runtime_user')
\gexec
SELECT format('REVOKE ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA public FROM %I', :'audit_operator_user')
\gexec
SELECT format(
    'GRANT EXECUTE ON FUNCTION public.purge_audit_entries_before(timestamptz, integer) TO %I',
    :'audit_operator_user'
)
WHERE to_regprocedure('public.purge_audit_entries_before(timestamptz,integer)') IS NOT NULL
\gexec

SELECT format(
    'ALTER DEFAULT PRIVILEGES FOR ROLE %I IN SCHEMA public REVOKE ALL ON TABLES FROM PUBLIC',
    :'migration_user'
)
\gexec
SELECT format(
    'ALTER DEFAULT PRIVILEGES FOR ROLE %I IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO %I',
    :'migration_user',
    :'runtime_user'
)
\gexec
SELECT format(
    'ALTER DEFAULT PRIVILEGES FOR ROLE %I IN SCHEMA public REVOKE ALL ON SEQUENCES FROM PUBLIC',
    :'migration_user'
)
\gexec
SELECT format(
    'ALTER DEFAULT PRIVILEGES FOR ROLE %I IN SCHEMA public GRANT USAGE, SELECT ON SEQUENCES TO %I',
    :'migration_user',
    :'runtime_user'
)
\gexec
SELECT format(
    'ALTER DEFAULT PRIVILEGES FOR ROLE %I IN SCHEMA public REVOKE EXECUTE ON FUNCTIONS FROM PUBLIC',
    :'migration_user'
)
\gexec
SELECT format(
    'ALTER DEFAULT PRIVILEGES FOR ROLE %I IN SCHEMA public REVOKE ALL ON FUNCTIONS FROM %I',
    :'migration_user',
    :'runtime_user'
)
\gexec
