\set ON_ERROR_STOP on
\getenv migration_user POSTGRES_MIGRATION_USER
SELECT set_config('upw.migration_user', :'migration_user', false) AS migration_setting
\gset

DO $$
DECLARE
    migration_record record;
    role_record record;
    table_record record;
BEGIN
    SELECT rolcanlogin, rolinherit, rolsuper, rolcreatedb, rolcreaterole, rolreplication, rolbypassrls
    INTO STRICT migration_record
    FROM pg_roles
    WHERE rolname = current_setting('upw.migration_user');

    IF NOT migration_record.rolcanlogin OR migration_record.rolinherit OR
       migration_record.rolsuper OR migration_record.rolcreatedb OR migration_record.rolcreaterole OR
       migration_record.rolreplication OR migration_record.rolbypassrls THEN
        RAISE EXCEPTION 'migration owner has privileged role attributes';
    END IF;
    IF EXISTS (
        SELECT 1
        FROM pg_auth_members
        JOIN pg_roles AS member ON member.oid = pg_auth_members.member
        WHERE member.rolname = current_setting('upw.migration_user')
    ) THEN
        RAISE EXCEPTION 'migration owner belongs to another role';
    END IF;

    SELECT rolcanlogin, rolinherit, rolsuper, rolcreatedb, rolcreaterole, rolreplication, rolbypassrls
    INTO STRICT role_record
    FROM pg_roles
    WHERE rolname = current_user;

    IF NOT role_record.rolcanlogin OR role_record.rolinherit OR
       role_record.rolsuper OR role_record.rolcreatedb OR role_record.rolcreaterole OR
       role_record.rolreplication OR role_record.rolbypassrls THEN
        RAISE EXCEPTION 'runtime role has privileged role attributes';
    END IF;
    IF EXISTS (
        SELECT 1
        FROM pg_auth_members
        JOIN pg_roles AS member ON member.oid = pg_auth_members.member
        WHERE member.rolname = current_user
    ) THEN
        RAISE EXCEPTION 'runtime role belongs to another role';
    END IF;

    IF pg_get_userbyid((SELECT datdba FROM pg_database WHERE datname = current_database())) <> current_setting('upw.migration_user') THEN
        RAISE EXCEPTION 'migration role does not own the database';
    END IF;
    IF pg_get_userbyid((SELECT nspowner FROM pg_namespace WHERE nspname = 'public')) <> current_setting('upw.migration_user') THEN
        RAISE EXCEPTION 'migration role does not own the public schema';
    END IF;
    IF has_database_privilege(current_user, current_database(), 'CREATE') OR
       has_database_privilege(current_user, current_database(), 'TEMPORARY') THEN
        RAISE EXCEPTION 'runtime role can create database objects or temporary tables';
    END IF;
    IF has_schema_privilege(current_user, 'public', 'CREATE') OR
       NOT has_schema_privilege(current_user, 'public', 'USAGE') THEN
        RAISE EXCEPTION 'runtime schema privileges are unsafe';
    END IF;
    IF to_regclass('public.alembic_version') IS NULL THEN
        RAISE EXCEPTION 'database has not been migrated';
    END IF;
    IF to_regclass('public.audit_entry') IS NULL THEN
        RAISE EXCEPTION 'audit table is missing';
    END IF;

    FOR table_record IN
        SELECT schemaname, tablename, tableowner
        FROM pg_tables
        WHERE schemaname = 'public'
    LOOP
        IF table_record.tableowner <> current_setting('upw.migration_user') THEN
            RAISE EXCEPTION 'migration role does not own table %.%', table_record.schemaname, table_record.tablename;
        END IF;
        IF table_record.tablename = 'alembic_version' THEN
            IF NOT has_table_privilege(current_user, 'public.alembic_version', 'SELECT') OR
               has_table_privilege(current_user, 'public.alembic_version', 'INSERT') OR
               has_table_privilege(current_user, 'public.alembic_version', 'UPDATE') OR
               has_table_privilege(current_user, 'public.alembic_version', 'DELETE') OR
               has_table_privilege(current_user, 'public.alembic_version', 'TRUNCATE') OR
               has_table_privilege(current_user, 'public.alembic_version', 'REFERENCES') OR
               has_table_privilege(current_user, 'public.alembic_version', 'TRIGGER') THEN
                RAISE EXCEPTION 'migration metadata privileges are unsafe';
            END IF;
        ELSIF table_record.tablename = 'audit_entry' THEN
            IF NOT has_table_privilege(current_user, 'public.audit_entry', 'SELECT') OR
               NOT has_table_privilege(current_user, 'public.audit_entry', 'INSERT') OR
               has_table_privilege(current_user, 'public.audit_entry', 'UPDATE') OR
               has_table_privilege(current_user, 'public.audit_entry', 'DELETE') OR
               has_table_privilege(current_user, 'public.audit_entry', 'TRUNCATE') OR
               has_table_privilege(current_user, 'public.audit_entry', 'REFERENCES') OR
               has_table_privilege(current_user, 'public.audit_entry', 'TRIGGER') THEN
                RAISE EXCEPTION 'audit table privileges are unsafe';
            END IF;
        ELSE
            IF NOT has_table_privilege(current_user, format('%I.%I', table_record.schemaname, table_record.tablename), 'SELECT') OR
               NOT has_table_privilege(current_user, format('%I.%I', table_record.schemaname, table_record.tablename), 'INSERT') OR
               NOT has_table_privilege(current_user, format('%I.%I', table_record.schemaname, table_record.tablename), 'UPDATE') OR
               NOT has_table_privilege(current_user, format('%I.%I', table_record.schemaname, table_record.tablename), 'DELETE') OR
               has_table_privilege(current_user, format('%I.%I', table_record.schemaname, table_record.tablename), 'TRUNCATE') OR
               has_table_privilege(current_user, format('%I.%I', table_record.schemaname, table_record.tablename), 'REFERENCES') OR
               has_table_privilege(current_user, format('%I.%I', table_record.schemaname, table_record.tablename), 'TRIGGER') THEN
                RAISE EXCEPTION 'ordinary table privileges are unsafe for %.%', table_record.schemaname, table_record.tablename;
            END IF;
        END IF;
    END LOOP;

    IF EXISTS (
        SELECT 1
        FROM pg_class
        JOIN pg_namespace ON pg_namespace.oid = pg_class.relnamespace
        WHERE pg_namespace.nspname = 'public'
          AND pg_get_userbyid(pg_class.relowner) <> current_setting('upw.migration_user')
    ) THEN
        RAISE EXCEPTION 'migration role does not own every public schema object';
    END IF;
    IF EXISTS (
        SELECT 1
        FROM pg_proc
        JOIN pg_namespace ON pg_namespace.oid = pg_proc.pronamespace
        WHERE pg_namespace.nspname = 'public'
          AND pg_get_userbyid(pg_proc.proowner) <> current_setting('upw.migration_user')
    ) THEN
        RAISE EXCEPTION 'migration role does not own every public function';
    END IF;
END
$$;
