"""Corrective readiness checks against isolated test records."""
from .test_milestone3_analytics import _Base


class HomepageTests(_Base):
    def test_priority_and_totals_reconcile_with_filtered_cases(self):
        self._case(self.rb, overdue=True)
        self._case(self.pg, status='under_review')
        self._case(self.rb, institution=self.inst2, status='awaiting_response')
        self.client.force_authenticate(self.coord)
        dashboard = self.client.get('/api/dashboard?region=South').data
        for metric, query in [('total', ''), ('pending', '&pending=true'),
                              ('under_process', '&under_process=true'), ('disposed', '&closed=true')]:
            self.assertEqual(dashboard[metric], self.client.get('/api/cases?region=South' + query).data['count'])
        priority = dashboard['management']['priority_institutions']
        self.assertEqual(len(priority), 1)
        self.assertEqual(priority[0]['count'], 2)
        self.assertEqual(priority[0]['overdue'], 1)
        self.assertEqual(str(priority[0]['institution_id']), str(self.inst.pk))

    def test_officers_receive_no_management_payload(self):
        self._case(self.pg)
        self.client.force_authenticate(self.rb_officer)
        data = self.client.get('/api/dashboard').data
        self.assertEqual(data['total'], 0)
        self.assertNotIn('management', data)
        self.assertNotIn('coordination_institutions', data)
