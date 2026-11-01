import unittest
from tests.research.recall import known_positive_metrics


class RecallTests(unittest.TestCase):
    def test_unknown_is_not_perfect_and_ground_truth_requires_independence(self):
        records=[{'id':key,'entity':{'name':'Genuine source entity','type':'institution'}} for key in ['a','b']]
        self.assertIsNone(known_positive_metrics(records,[],{}, {})['recall_at5'])
        row={'pair_id':'ab','query_id':'a','reference_id':'b','incident_family':'reviewed-event',
             'permission_reference':'authorization-123','established_before_retrieval':True,
             'reviewer_1':'real-reviewer-a','reviewer_2':'real-reviewer-b','label_1':'same_incident','label_2':'same_incident',
             'final_label':'same_incident','status':'agreed','reason':'Synthetic validator fixture, not a real judgment','evidence_references':'fictional-source'}
        result=known_positive_metrics(records,[row],{'a':[]},{'a':['b']})
        self.assertEqual(result['recall_at5'],0); self.assertEqual(result['candidate_recall'],1)
        row['reviewer_2']='real-reviewer-a'
        with self.assertRaises(ValueError): known_positive_metrics(records,[row],{}, {})
