from django.db import migrations


SQL = r"""
CREATE FUNCTION protect_reviewed_fact() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE source_text text;
BEGIN
  IF TG_OP = 'DELETE' THEN RAISE EXCEPTION 'Fact evidence is protected; append a correction'; END IF;
  IF TG_OP = 'UPDATE' AND
    (to_jsonb(NEW) - ARRAY['state','reviewer_id','reviewed_at','reason','version']) IS DISTINCT FROM
    (to_jsonb(OLD) - ARRAY['state','reviewer_id','reviewed_at','reason','version']) THEN
    RAISE EXCEPTION 'Original fact evidence is immutable';
  END IF;
  IF NEW.kind NOT IN ('incident_date','reference','remedy') OR NEW.source_field NOT IN ('summary','description','source_reference') THEN
    RAISE EXCEPTION 'Unsupported fact evidence';
  END IF;
  IF TG_OP = 'INSERT' OR NEW.state = 'accepted' THEN
  SELECT CASE NEW.source_field WHEN 'summary' THEN summary WHEN 'description' THEN description ELSE source_reference END
    INTO source_text FROM cases_complaint WHERE id=NEW.case_id FOR SHARE;
  IF NEW.span_end > char_length(source_text) OR NEW.quote IS DISTINCT FROM substring(source_text FROM NEW.span_start+1 FOR NEW.span_end-NEW.span_start)
    OR NEW.source_digest IS DISTINCT FROM encode(sha256(convert_to(source_text,'UTF8')),'hex') THEN
    RAISE EXCEPTION 'Fact source span or digest does not match';
  END IF;
  END IF;
  RETURN NEW;
END $$;
CREATE TRIGGER reviewed_fact_protection BEFORE INSERT OR UPDATE OR DELETE ON cases_reviewedfact
  FOR EACH ROW EXECUTE FUNCTION protect_reviewed_fact();

CREATE FUNCTION protect_incident_membership() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE group_institution uuid; case_institution uuid;
BEGIN
  IF TG_OP = 'DELETE' THEN RAISE EXCEPTION 'Incident membership is protected; mark inactive'; END IF;
  IF TG_OP = 'UPDATE' AND (NEW.group_id <> OLD.group_id OR NEW.case_id <> OLD.case_id) THEN
    RAISE EXCEPTION 'Membership identity is immutable';
  END IF;
  SELECT institution_id INTO group_institution FROM cases_incidentgroup WHERE id=NEW.group_id FOR SHARE;
  SELECT institution_id INTO case_institution FROM cases_complaint WHERE id=NEW.case_id FOR SHARE;
  IF group_institution IS DISTINCT FROM case_institution THEN RAISE EXCEPTION 'Incident members must share an institution'; END IF;
  RETURN NEW;
END $$;
CREATE TRIGGER incident_membership_protection BEFORE INSERT OR UPDATE OR DELETE ON cases_incidentmembership
  FOR EACH ROW EXECUTE FUNCTION protect_incident_membership();

CREATE FUNCTION protect_incident_group() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  IF TG_OP = 'DELETE' THEN RAISE EXCEPTION 'Incident groups are protected'; END IF;
  IF NEW.institution_id <> OLD.institution_id OR NEW.submission_id <> OLD.submission_id THEN
    RAISE EXCEPTION 'Group identity is immutable';
  END IF;
  RETURN NEW;
END $$;
CREATE TRIGGER incident_group_protection BEFORE UPDATE OR DELETE ON cases_incidentgroup
  FOR EACH ROW EXECUTE FUNCTION protect_incident_group();

CREATE FUNCTION protect_grouped_case_institution() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  IF NEW.institution_id <> OLD.institution_id AND EXISTS (
    SELECT 1 FROM cases_incidentmembership m JOIN cases_incidentgroup g ON g.id=m.group_id
    WHERE m.case_id=NEW.id AND g.institution_id <> NEW.institution_id) THEN
    RAISE EXCEPTION 'Protected incident membership forbids moving canonical institution';
  END IF;
  RETURN NEW;
END $$;
CREATE TRIGGER grouped_case_institution BEFORE UPDATE OF institution_id ON cases_complaint
  FOR EACH ROW EXECUTE FUNCTION protect_grouped_case_institution();
"""

REVERSE = """
DROP TRIGGER grouped_case_institution ON cases_complaint;
DROP FUNCTION protect_grouped_case_institution();
DROP TRIGGER incident_group_protection ON cases_incidentgroup;
DROP FUNCTION protect_incident_group();
DROP TRIGGER incident_membership_protection ON cases_incidentmembership;
DROP FUNCTION protect_incident_membership();
DROP TRIGGER reviewed_fact_protection ON cases_reviewedfact;
DROP FUNCTION protect_reviewed_fact();
"""


class Migration(migrations.Migration):
    dependencies = [('cases', '0014_case_intelligence')]
    operations = [migrations.RunSQL(SQL, REVERSE)]
