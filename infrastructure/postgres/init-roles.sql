\set ON_ERROR_STOP on
\getenv database_name POSTGRES_DB
\getenv migration_user POSTGRES_MIGRATION_USER
\getenv migration_password POSTGRES_MIGRATION_PASSWORD
\getenv runtime_user POSTGRES_RUNTIME_USER
\getenv runtime_password POSTGRES_RUNTIME_PASSWORD
\getenv audit_operator_user POSTGRES_AUDIT_OPERATOR_USER
\getenv audit_operator_password POSTGRES_AUDIT_OPERATOR_PASSWORD

SELECT format(
    'CREATE ROLE %I LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT NOREPLICATION NOBYPASSRLS PASSWORD %L',
    :'migration_user',
    :'migration_password'
)
WHERE NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = :'migration_user')
\gexec

SELECT format(
    'ALTER ROLE %I WITH LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT NOREPLICATION NOBYPASSRLS PASSWORD %L',
    :'migration_user',
    :'migration_password'
)
\gexec

SELECT format(
    'CREATE ROLE %I LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT NOREPLICATION NOBYPASSRLS PASSWORD %L',
    :'audit_operator_user',
    :'audit_operator_password'
)
WHERE NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = :'audit_operator_user')
\gexec

SELECT format(
    'ALTER ROLE %I WITH LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT NOREPLICATION NOBYPASSRLS PASSWORD %L',
    :'audit_operator_user',
    :'audit_operator_password'
)
\gexec

SELECT format(
    'CREATE ROLE %I LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT NOREPLICATION NOBYPASSRLS PASSWORD %L',
    :'runtime_user',
    :'runtime_password'
)
WHERE NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = :'runtime_user')
\gexec

SELECT format(
    'ALTER ROLE %I WITH LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT NOREPLICATION NOBYPASSRLS PASSWORD %L',
    :'runtime_user',
    :'runtime_password'
)
\gexec

SELECT format('REVOKE %I FROM %I', parent.rolname, member.rolname)
FROM pg_auth_members AS membership
JOIN pg_roles AS parent ON parent.oid = membership.roleid
JOIN pg_roles AS member ON member.oid = membership.member
WHERE member.rolname IN (:'migration_user', :'runtime_user', :'audit_operator_user')
\gexec

SELECT format(
    'ALTER %s %I.%I OWNER TO %I',
    CASE pg_class.relkind
        WHEN 'r' THEN 'TABLE'
        WHEN 'p' THEN 'TABLE'
        WHEN 'S' THEN 'SEQUENCE'
        WHEN 'v' THEN 'VIEW'
        WHEN 'm' THEN 'MATERIALIZED VIEW'
        WHEN 'f' THEN 'FOREIGN TABLE'
    END,
    pg_namespace.nspname,
    pg_class.relname,
    :'migration_user'
)
FROM pg_class
JOIN pg_namespace ON pg_namespace.oid = pg_class.relnamespace
WHERE pg_namespace.nspname = 'public'
  AND pg_get_userbyid(pg_class.relowner) = current_user
  AND pg_class.relkind IN ('r', 'p', 'S', 'v', 'm', 'f')
ORDER BY CASE WHEN pg_class.relkind IN ('r', 'p') THEN 0 ELSE 1 END, pg_class.relname
\gexec

SELECT format(
    'ALTER ROUTINE %I.%I(%s) OWNER TO %I',
    pg_namespace.nspname,
    pg_proc.proname,
    pg_get_function_identity_arguments(pg_proc.oid),
    :'migration_user'
)
FROM pg_proc
JOIN pg_namespace ON pg_namespace.oid = pg_proc.pronamespace
WHERE pg_namespace.nspname = 'public'
  AND pg_get_userbyid(pg_proc.proowner) = current_user
\gexec

SELECT format(
    'ALTER TYPE %I.%I OWNER TO %I',
    pg_namespace.nspname,
    pg_type.typname,
    :'migration_user'
)
FROM pg_type
JOIN pg_namespace ON pg_namespace.oid = pg_type.typnamespace
WHERE pg_namespace.nspname = 'public'
  AND pg_get_userbyid(pg_type.typowner) = current_user
  AND pg_type.typrelid = 0
  AND pg_type.typtype IN ('c', 'd', 'e', 'm', 'r')
\gexec

SELECT format('ALTER DATABASE %I OWNER TO %I', :'database_name', :'migration_user')
\gexec
SELECT format('ALTER SCHEMA public OWNER TO %I', :'migration_user')
\gexec

SELECT format('REVOKE ALL PRIVILEGES ON DATABASE %I FROM PUBLIC', :'database_name')
\gexec
SELECT format('REVOKE ALL PRIVILEGES ON DATABASE %I FROM %I', :'database_name', :'runtime_user')
\gexec
SELECT format('GRANT CONNECT ON DATABASE %I TO %I', :'database_name', :'runtime_user')
\gexec
SELECT format('GRANT CONNECT ON DATABASE %I TO %I', :'database_name', :'audit_operator_user')
\gexec
SELECT format('GRANT CONNECT, CREATE, TEMPORARY ON DATABASE %I TO %I', :'database_name', :'migration_user')
\gexec

REVOKE ALL PRIVILEGES ON SCHEMA public FROM PUBLIC;
SELECT format('REVOKE ALL PRIVILEGES ON SCHEMA public FROM %I', :'runtime_user')
\gexec
SELECT format('GRANT USAGE ON SCHEMA public TO %I', :'runtime_user')
\gexec
SELECT format('GRANT USAGE ON SCHEMA public TO %I', :'audit_operator_user')
\gexec
SELECT format('GRANT ALL PRIVILEGES ON SCHEMA public TO %I', :'migration_user')
\gexec

SELECT format('ALTER ROLE %I SET search_path = public, pg_catalog', :'migration_user')
\gexec
SELECT format('ALTER ROLE %I SET search_path = public, pg_catalog', :'runtime_user')
\gexec
SELECT format('ALTER ROLE %I SET search_path = public, pg_catalog', :'audit_operator_user')
\gexec
