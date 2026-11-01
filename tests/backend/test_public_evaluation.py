import csv
import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import patch
import numpy as np
from tests.research.public_corpus import collect, normalize_cfpb, normalize_nyc, validate_manifest, redact
from tests.research.public_corpus import digest
from tests.research.public_evaluation import validate_records, split_records, final_labels, summarize, evaluate_workspace, blind_files, workflow_counts


def manifest():
    return {'private_storage': True, 'sources': [{'dataset': 'nyc311', 'source_url': 'https://data.cityofnewyork.us/resource/erm2-nwe9.json',
        'terms_url': 'https://nyc.gov', 'usage_conditions': 'Public research fixture, not actual downloaded text',
        'collected_at_utc': '2026-11-01T00:00:00Z', 'evaluation_permitted': True, 'status': 'collected', 'response': {'sha256': '0'*64}}]}


class PublicEvaluationTests(unittest.TestCase):
    def workspace(self, root, rows):
        raw=json.dumps(rows).encode('utf-8')
        (root/'corpus.json').write_bytes(raw)
        value=manifest();value['corpus_sha256']=digest(raw)
        (root/'manifest.json').write_text(json.dumps(value),encoding='utf-8')

    def records(self):
        return normalize_nyc([{'unique_key': str(i), 'agency': 'TEST', 'complaint_type': f'Fictional category {i}',
            'descriptor': 'Synthetic fixture', 'created_date': '2026-09-01T00:00:00', 'status': 'Closed', 'closed_date': '2026-09-02T00:00:00',
            'incident_address': 'Do not collect this field', 'latitude': 1.0} for i in range(20)])

    def test_minimal_fields_preserve_source_and_never_invent_institutions(self):
        records = self.records(); validate_records(records, manifest())
        row = records[0]
        self.assertIsNone(row['institution_id']); self.assertIsNone(row['original_text'])
        self.assertNotIn('incident_address',row['original_fields']); self.assertNotIn('latitude',row['original_fields'])
        self.assertEqual(row['text_type'],'structured_request_fields')
        row['institution_id'] = 'FAKE-COLLEGE'
        with self.assertRaises(ValueError): validate_records(records,manifest())

    def test_missing_permissions_and_checksums_reject_collection_manifest(self):
        for key in ['usage_conditions','terms_url','evaluation_permitted','response']:
            value = manifest(); value['sources'][0].pop(key)
            with self.assertRaises(ValueError): validate_manifest(value)
        for invalid in [None,{'sha256':'bad'}]:
            value=manifest();value['sources'][0]['response']=invalid
            with self.assertRaises(ValueError):validate_manifest(value)

    def test_source_timeouts_are_manifested_and_do_not_discard_other_source_statuses(self):
        with TemporaryDirectory() as directory, patch('tests.research.public_corpus.fetch',side_effect=TimeoutError('Public source unavailable')):
            result=collect(Path(directory)/'private')
            self.assertEqual([s['status'] for s in result['sources']],['pending_permission','blocked','blocked'])
            self.assertTrue((Path(directory)/'private'/'manifest.json').exists())

    def test_duplicate_source_records_are_not_independent_complaints(self):
        rows=self.records(); rows[1]['source_id']=rows[0]['source_id']
        with self.assertRaises(ValueError): validate_records(rows,manifest())

    def test_query_reference_separation_keeps_exact_text_groups_together(self):
        rows=self.records(); duplicate={**rows[0],'id':'new-id','source_id':'new-source'}; rows.append(duplicate)
        q,r,_=split_records(rows)
        self.assertFalse({v['id'] for v in q}&{v['id'] for v in r})
        self.assertFalse({v['model_text'].casefold() for v in q}&{v['model_text'].casefold() for v in r})
        self.assertTrue(all(v['incident_group'] is None for v in q+r))

    def test_original_narrative_is_retained_privately_and_redactions_are_recorded(self):
        rows=normalize_cfpb([{'complaint_id':'fictional','company':'Example company','complaint_what_happened':'Contact test@example.invalid about 1234567890123.'}])
        self.assertIn('test@example.invalid',rows[0]['original_text'])
        self.assertNotIn('test@example.invalid',rows[0]['model_text'])
        self.assertTrue(rows[0]['redactions']); self.assertIsNone(rows[0]['institution_id'])
        self.assertEqual(rows[0]['entity']['type'],'company')

    def annotation(self, **updates):
        return {'pair_id':'pair','reviewer_1':'one','reviewer_2':'two','label_1':'related_issue','label_2':'related_issue',
            'final_label':'related_issue','adjudicator':'','reason':'Independent rationale','evidence_references':'source-a;source-b','status':'agreed',**updates}

    def test_annotation_requires_independence_and_real_adjudication(self):
        self.assertEqual(final_labels([self.annotation()],{'pair'}),{'pair':'related_issue'})
        for changes in [{'reviewer_2':'one'},{'reason':''},{'evidence_references':''},{'final_label':'duplicate'},
                        {'label_2':'unrelated','status':'adjudicated','adjudicator':'one'}]:
            with self.assertRaises(ValueError): final_labels([self.annotation(**changes)],{'pair'})
        self.assertEqual(final_labels([self.annotation(label_2='unrelated',status='adjudicated',adjudicator='third')],{'pair'}),{'pair':'related_issue'})

    def test_uncertain_and_missing_labels_never_become_negatives(self):
        rows=[{'query_id':'q','pair_id':'a'},{'query_id':'q','pair_id':'b'}]
        result=summarize(rows,{'a':'insufficient_evidence'},1)
        self.assertIsNone(result['review_worthy_precision_at_5']); self.assertEqual(result['usable_label_coverage'],0)
        self.assertEqual(result['insufficient_evidence'],1); self.assertEqual(result['unjudged'],1)
        self.assertIsNone(result['same_incident_recall_at_5']); self.assertIsNone(result['false_positive_rate'])

    def test_precision_denominators_and_zero_suggestion_abstention(self):
        rows=[{'query_id':'q1','pair_id':'a'},{'query_id':'q2','pair_id':'b'}]
        result=summarize(rows,{'a':'same_incident','b':'unrelated'},4)
        self.assertEqual(result['review_worthy_precision_at_5'],.5); self.assertEqual(result['usable_label_coverage'],1)
        self.assertEqual(result['no_suggestion_rate'],.5); self.assertIsNotNone(result['precision_interval'])
        self.assertEqual(summarize([],{},3)['no_suggestion_rate'],1)

    def test_blind_annotation_excludes_scores_and_escapes_spreadsheet_formulas(self):
        rows=self.records(); rows[0]['model_text']='=DANGEROUS()'
        with TemporaryDirectory() as directory:
            blind_files(Path(directory),'nyc311',[{'pair_id':'a','query_id':rows[0]['id'],'reference_id':rows[1]['id'],'cosine':.9}],{r['id']:r for r in rows})
            with (Path(directory)/'nyc311-reviewer-1.csv').open() as source: result=list(csv.DictReader(source))
            self.assertNotIn('cosine',result[0]); self.assertTrue(result[0]['text_a'].startswith("'="))
            self.assertEqual(result[0]['label'],'')

    def test_workflow_dates_are_not_aicte_deadlines_or_bureau_assignments(self):
        result=workflow_counts(self.records())
        self.assertEqual(result['unique_source_keys'],20); self.assertEqual(result['mean_recorded_closure_days'],1)
        self.assertNotIn('overdue',result); self.assertNotIn('bureau',result)

    def test_evaluation_is_local_non_mutating_and_preserves_unknown_metrics(self):
        with TemporaryDirectory() as directory:
            root=Path(directory); rows=self.records()
            self.workspace(root,rows)
            before=(root/'corpus.json').read_bytes()
            encoder=SimpleNamespace(encode=lambda texts,**kwargs:np.ones((len(texts),384)))
            tokenizer=SimpleNamespace(encode=lambda text:SimpleNamespace(ids=list(range(10))))
            with patch('tests.research.public_corpus.fetch',side_effect=AssertionError('Evaluation must not make HTTP requests')):
                result=evaluate_workspace(root,encoder,tokenizer)
            self.assertFalse(result['database_access']); self.assertFalse(result['production_policy_changed'])
            self.assertEqual(result['tracks']['nyc311']['queries_without_eligible_references'],0)
            self.assertIsNone(result['tracks']['nyc311']['metrics']['review_worthy_precision_at_5'])
            self.assertEqual((root/'corpus.json').read_bytes(),before)
            with self.assertRaises(FileExistsError):evaluate_workspace(root,encoder,tokenizer)

    def test_long_narratives_are_excluded_without_silent_truncation(self):
        with TemporaryDirectory() as directory:
            root=Path(directory)
            self.workspace(root,self.records())
            encoder=SimpleNamespace(encode=lambda *a,**k: (_ for _ in ()).throw(AssertionError('Must not encode overlong inputs')))
            tokenizer=SimpleNamespace(encode=lambda text:SimpleNamespace(ids=list(range(257))))
            result=evaluate_workspace(root,encoder,tokenizer)['tracks']['nyc311']
            self.assertEqual(result['token_limit_exclusions'],20); self.assertEqual(result['eligible_records'],0)
