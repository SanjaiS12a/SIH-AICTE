import csv
import io
import json
from django.db import connection
from django.test.utils import CaptureQueriesContext
from cases.models import CaseAction, Membership
from .test_milestone3_analytics import _Base


class MovementExportTests(_Base):
    def export(self):
        response=self.client.get('/api/movements.csv')
        self.assertEqual(response.status_code,200)
        body=b''.join(response.streaming_content).decode('utf-8')
        return body,list(csv.DictReader(io.StringIO(body)))

    def test_query_count_does_not_grow_with_export_rows(self):
        case=self._case(self.rb)
        self.client.force_authenticate(self.coord)
        CaseAction.objects.bulk_create([CaseAction(case=case,actor=self.coord,kind='note',reason=f'Initial {i}') for i in range(2)])
        with CaptureQueriesContext(connection) as small:
            _,rows=self.export()
        self.assertEqual(len(rows),2)
        CaseAction.objects.bulk_create([CaseAction(case=case,actor=self.coord,kind='note',reason=f'Additional {i}') for i in range(98)])
        with CaptureQueriesContext(connection) as large:
            _,rows=self.export()
        self.assertEqual(len(rows),100)
        self.assertLessEqual(len(large),len(small)+2,'Export permissions/serialization must not query once per action.')

    def test_roles_and_current_membership_preserve_redaction_and_history(self):
        own=self._case(self.rb);hidden=self._case(self.pg)
        for case,reason in [(own,'Authorized note'),(hidden,'Other Bureau confidential note')]:
            CaseAction.objects.create(case=case,actor=self.coord,kind='note',reason=reason)
        CaseAction.objects.create(case=own,actor=self.coord,kind='overlap_review',reason='Restricted pair rationale',changes={'hidden_reference':hidden.reference})
        CaseAction.objects.create(case=own,actor=self.coord,kind='coordination_group_changed',reason='Restricted group rationale',changes={'group_id':'restricted-group'})
        for actor in [self.coord,self.auditor]:
            self.client.force_authenticate(actor)
            body,rows=self.export()
            self.assertEqual(len(rows),4)
            self.assertIn('Restricted pair rationale',body)
            self.assertIn('restricted-group',body)
        self.client.force_authenticate(self.rb_officer)
        body,rows=self.export()
        self.assertEqual(len(rows),2)
        self.assertNotIn(hidden.reference,body)
        self.assertNotIn('Restricted pair rationale',body)
        self.assertNotIn('restricted-group',body)
        pair=next(row for row in rows if row['Event']=='overlap_review')
        self.assertEqual(json.loads(pair['Changes']),{})
        self.assertEqual(pair['Bureau at action'],'RB')
        Membership.objects.filter(user=self.rb_officer).update(bureau=self.pg)
        _,rows=self.export()
        self.assertEqual([row['Case'] for row in rows],[hidden.reference])
        self.client.force_authenticate(self.coord)
        moved=self.client.post(f'/api/cases/{own.pk}/actions',{'kind':'transfer','bureau':'PGRC','expected_version':own.version,'reason':'Current ownership changed'},format='json')
        self.assertEqual(moved.status_code,200,moved.data)
        self.client.force_authenticate(self.rb_officer)
        body,rows=self.export()
        self.assertEqual({row['Case'] for row in rows},{own.reference,hidden.reference})
        self.assertNotIn('restricted-group',body)
        transferred=next(row for row in rows if row['Event']=='transfer')
        self.assertEqual(transferred['Bureau at action'],'PGRC')

    def test_csv_values_remain_equivalent_to_authorized_movements(self):
        case=self._case(self.rb)
        CaseAction.objects.create(case=case,actor=self.coord,kind='note',reason='=SUM(1,2)\nQuoted "evidence"',changes={'note':'two, values'})
        CaseAction.objects.create(case=case,actor=self.coord,kind='status',reason='Closed following response',changes={'status':{'before':'under_review','after':'disposed'}})
        self.client.force_authenticate(self.coord)
        _,rows=self.export()
        listed=self.client.get('/api/movements').data['results']
        self.assertEqual(len(rows),len(listed))
        for csv_row,action in zip(rows,listed):
            expected_reason="'"+action['reason'] if action['reason'].lstrip().startswith(('=','+','-','@')) else action['reason']
            self.assertEqual(csv_row['Reason'],expected_reason)
            self.assertEqual(csv_row['Actor'],action['actor'])
            self.assertEqual(csv_row['Event'],action['event'])
            self.assertEqual(json.loads(csv_row['Changes']),action['changes'])
            self.assertEqual(csv_row['Action time'],action['created_at'])
