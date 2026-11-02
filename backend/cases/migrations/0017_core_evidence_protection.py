"""Preserve source-span protections while admitting additional literal fact types."""
from importlib import import_module
from django.db import migrations


original_fact = import_module('cases.migrations.0015_intelligence_protection').SQL.split('CREATE TRIGGER reviewed_fact_protection')[0]
original_fact = original_fact.replace('CREATE FUNCTION protect_reviewed_fact()', 'CREATE OR REPLACE FUNCTION protect_reviewed_fact()')
extended_fact = original_fact.replace("'incident_date','reference','remedy'", "'incident_date','reference','remedy','academic_year','allegation','topic'")

GROUP = """
CREATE FUNCTION protect_coordination_incident() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE g cases_incidentgroup%ROWTYPE;
BEGIN
  IF TG_OP='UPDATE' AND (NEW.incident_group_id IS DISTINCT FROM OLD.incident_group_id OR NEW.incident_group_version IS DISTINCT FROM OLD.incident_group_version) THEN
    RAISE EXCEPTION 'Coordination source incident snapshot is immutable';
  END IF;
  IF NEW.incident_group_id IS NOT NULL THEN
    SELECT * INTO g FROM cases_incidentgroup WHERE id=NEW.incident_group_id FOR SHARE;
    IF g.institution_id IS DISTINCT FROM NEW.institution_id THEN RAISE EXCEPTION 'Coordination incident must share its institution'; END IF;
    IF TG_OP='INSERT' AND (g.state <> 'active' OR g.needs_review OR g.version <> NEW.incident_group_version) THEN
      RAISE EXCEPTION 'Coordination needs a current reviewed incident snapshot';
    END IF;
  END IF;
  RETURN NEW;
END $$;
CREATE TRIGGER coordination_incident_protection BEFORE INSERT OR UPDATE ON cases_coordinationrecord
  FOR EACH ROW EXECUTE FUNCTION protect_coordination_incident();
"""


class Migration(migrations.Migration):
    dependencies = [('cases','0016_core_incident_counts')]
    operations = [migrations.RunSQL(extended_fact + GROUP,
        'DROP TRIGGER coordination_incident_protection ON cases_coordinationrecord; DROP FUNCTION protect_coordination_incident();' + original_fact)]
