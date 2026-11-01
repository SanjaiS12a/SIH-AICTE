from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [('cases', '0012_complaint_source_bureau_complaint_source_import_and_more')]
    operations = [
        migrations.AddField(model_name='caseaction', name='bureau_at_action',
            field=models.ForeignKey(null=True, editable=False, on_delete=django.db.models.deletion.PROTECT,
                related_name='historical_actions', to='cases.bureau')),
        migrations.RunSQL("""
            CREATE FUNCTION snapshot_action_bureau() RETURNS trigger LANGUAGE plpgsql AS $$
            BEGIN
                SELECT bureau_id INTO NEW.bureau_at_action_id FROM cases_complaint WHERE id = NEW.case_id FOR SHARE;
                RETURN NEW;
            END;
            $$;
            CREATE TRIGGER case_action_bureau_snapshot BEFORE INSERT ON cases_caseaction
                FOR EACH ROW EXECUTE FUNCTION snapshot_action_bureau();
        """, reverse_sql="""
            DROP TRIGGER case_action_bureau_snapshot ON cases_caseaction;
            DROP FUNCTION snapshot_action_bureau();
        """),
    ]
