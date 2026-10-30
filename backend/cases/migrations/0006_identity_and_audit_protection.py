from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [('cases', '0005_institution_contacts_version')]

    operations = [migrations.RunSQL(
        sql="""
        CREATE FUNCTION protect_institution_identity() RETURNS trigger LANGUAGE plpgsql AS $$
        BEGIN
            IF NEW.permanent_id IS DISTINCT FROM OLD.permanent_id THEN
                RAISE EXCEPTION 'Institution permanent ID is immutable' USING ERRCODE = '23514';
            END IF;
            RETURN NEW;
        END;
        $$;
        CREATE TRIGGER institution_identity_immutable BEFORE UPDATE ON cases_institution
            FOR EACH ROW EXECUTE FUNCTION protect_institution_identity();
        CREATE FUNCTION protect_action_history() RETURNS trigger LANGUAGE plpgsql AS $$
        BEGIN
            RAISE EXCEPTION 'Audit records are append-only; record a compensating action'
                USING ERRCODE = '23514';
        END;
        $$;
        CREATE TRIGGER case_actions_append_only BEFORE UPDATE OR DELETE ON cases_caseaction
            FOR EACH ROW EXECUTE FUNCTION protect_action_history();
        CREATE TRIGGER audit_events_append_only BEFORE UPDATE OR DELETE ON cases_auditevent
            FOR EACH ROW EXECUTE FUNCTION protect_action_history();
        """,
        reverse_sql="""
        DROP TRIGGER audit_events_append_only ON cases_auditevent;
        DROP TRIGGER case_actions_append_only ON cases_caseaction;
        DROP FUNCTION protect_action_history();
        DROP TRIGGER institution_identity_immutable ON cases_institution;
        DROP FUNCTION protect_institution_identity();
        """,
    )]
