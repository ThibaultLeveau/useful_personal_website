\set ON_ERROR_STOP on

DO $$
BEGIN
    IF has_database_privilege(current_user, current_database(), 'CREATE') OR
       has_database_privilege(current_user, current_database(), 'TEMPORARY') OR
       has_schema_privilege(current_user, 'public', 'CREATE') THEN
        RAISE EXCEPTION 'audit operator has object-creation privileges';
    END IF;
    IF NOT has_table_privilege(current_user, 'public.audit_entry', 'SELECT') OR
       NOT has_table_privilege(current_user, 'public.audit_entry', 'INSERT') OR
       has_table_privilege(current_user, 'public.audit_entry', 'UPDATE') OR
       has_table_privilege(current_user, 'public.audit_entry', 'DELETE') OR
       has_table_privilege(current_user, 'public.audit_entry', 'TRUNCATE') THEN
        RAISE EXCEPTION 'audit operator table privileges are unsafe';
    END IF;
    IF NOT has_function_privilege(
        current_user,
        'public.purge_audit_entries_before(timestamptz,integer)',
        'EXECUTE'
    ) THEN
        RAISE EXCEPTION 'audit operator cannot execute the bounded retention function';
    END IF;
END
$$;
