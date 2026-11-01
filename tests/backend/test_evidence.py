import io
import json
import uuid
from copy import deepcopy
from concurrent.futures import ThreadPoolExecutor
from datetime import date
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import patch
import numpy as np
from django.conf import settings
from django.contrib.auth.models import User
from django.core.management import call_command
from django.core.management.base import CommandError
from django.db import close_old_connections
from django.test import SimpleTestCase, TestCase, TransactionTestCase, override_settings
from django.utils import timezone
from rest_framework.test import APIClient
from cases.evidence import build_evidence, MATCHING_POLICY_REVISION
from cases.matching import match_case
from cases.models import Bureau, Institution, Membership, Complaint, CaseAction, OverlapCandidate
from cases.management.commands.evaluate_matching import eligible_corpus, evaluate


class EvidenceContractTests(SimpleTestCase):
    def cases(self, **changes):
        institution = SimpleNamespace(name='Fictional', permanent_id='TEST-1')
        fields = dict(pk='a', institution=institution, institution_id='institution', version=1,
                      source_system='RB-file', source_reference='', category='refunds',
                      classification='unclassified', incident_date=None)
        left = SimpleNamespace(**fields)
        right = SimpleNamespace(**{**fields, 'pk': 'b', **changes})
        return left, right

    def test_missing_references_are_unknown_in_semantic_and_manual_evidence(self):
        for value in ['', '   ', None]:
            left, right = self.cases(source_reference=value)
            left.source_reference = value
            for kwargs in [{}, {'score': .83, 'model_revision': 'encoder'}]:
                evidence = build_evidence(left, right, **kwargs)
                self.assertFalse(evidence['shared_reference'])
                self.assertEqual(evidence['comparisons']['source_reference']['state'], 'unknown')
                self.assertEqual(evidence['comparisons']['source_identity']['state'], 'unknown')

    def test_shared_text_is_not_shared_source_identity(self):
        left, right = self.cases(source_reference='REF-1', source_system='PGRC-file')
        left.source_reference = 'REF-1'
        evidence = build_evidence(left, right, score=.9, model_revision='encoder')
        self.assertTrue(evidence['shared_reference'])
        self.assertEqual(evidence['comparisons']['source_reference']['state'], 'agrees')
        self.assertEqual(evidence['comparisons']['source_identity']['state'], 'differs')
        self.assertEqual(evidence['incident_finding']['state'], 'unverified')
        right.source_system = left.source_system
        self.assertEqual(build_evidence(left, right)['comparisons']['source_identity']['state'], 'agrees')

    def test_versioned_provenance_and_disagreement_never_become_findings(self):
        left, right = self.cases(incident_date=date(2025, 1, 1), category='documents', classification='grievance')
        left.incident_date = date(2026, 1, 1)
        evidence = build_evidence(left, right, score=.75, model_revision='encoder')
        self.assertEqual(evidence['schema_version'], 1)
        self.assertEqual(evidence['matching_policy_revision'], MATCHING_POLICY_REVISION)
        self.assertEqual(evidence['cosine_score'], .75)
        self.assertEqual(evidence['encoder_revision'], 'encoder')
        self.assertEqual(evidence['canonical_institution']['state'], 'agrees')
        self.assertEqual(evidence['comparisons']['category']['state'], 'differs')
        self.assertEqual(evidence['comparisons']['incident_date']['state'], 'differs')
        self.assertEqual(evidence['comparisons']['classification']['state'], 'unknown')
        self.assertEqual(evidence['provenance']['left_case_id'], 'a')
        self.assertEqual(evidence['incident_finding']['state'], 'unverified')
        manual = build_evidence(left, right)
        self.assertIsNone(manual['cosine_score']); self.assertIsNone(manual['encoder_revision'])


class EvidenceFixture:
    def setUp(self):
        self.rb = Bureau.objects.create(code='RB', name='Regulation')
        self.pg = Bureau.objects.create(code='PGRC', name='Grievances')
        self.institution = Institution.objects.create(name='Fictional evidence college', permanent_id='EVIDENCE-1', region='South', district='Test')
        self.coordinator = User.objects.create_user('evidence-coordinator', first_name='Coordinator')
        Membership.objects.create(user=self.coordinator, role='coordinator')
        self.officer = User.objects.create_user('evidence-officer')
        Membership.objects.create(user=self.officer, role='officer', bureau=self.rb)
        self.auditor = User.objects.create_user('evidence-auditor')
        Membership.objects.create(user=self.auditor, role='auditor')
        self.left, self.right = sorted([self.make_case('A', self.rb), self.make_case('B', self.pg)], key=lambda c: c.pk)
        self.client = APIClient(); self.client.force_authenticate(self.coordinator)

    def make_case(self, ref, bureau):
        return Complaint.objects.create(reference=ref, source_system='evidence-test', source_reference=ref,
            submission_id=uuid.uuid4(), institution=self.institution, bureau=bureau, created_by=self.coordinator,
            category='refunds', summary='Refund withheld.', description='Fictional test.', received_at=timezone.now(), due_at=timezone.now())

    def pair(self, evidence=None, **extra):
        return OverlapCandidate.objects.create(left=self.left, right=self.right, score=.9, model_revision='encoder',
            evidence=evidence if evidence is not None else build_evidence(self.left, self.right, score=.9, model_revision='encoder'), **extra)

    def review(self, pair, **extra):
        return self.client.post(f'/api/overlaps/{pair.pk}/review', {
            'decision': 'related_issue', 'reason': 'Restricted cross-Bureau evidence', 'expected_version': pair.version, **extra}, format='json')


class EvidenceWorkflowTests(EvidenceFixture, TestCase):
    def test_both_histories_snapshot_exact_evidence_and_replay_is_idempotent(self):
        pair = self.pair()
        before = deepcopy(pair.evidence)
        self.assertEqual(self.review(pair).status_code, 200)
        actions = list(CaseAction.objects.filter(kind='overlap_review'))
        self.assertEqual(len(actions), 2)
        self.assertEqual(actions[0].changes['review_snapshot'], actions[1].changes['review_snapshot'])
        snapshot = actions[0].changes['review_snapshot']
        self.assertEqual(snapshot['evidence'], before)
        self.assertEqual(snapshot['matching_policy_revision'], MATCHING_POLICY_REVISION)
        self.assertEqual(snapshot['reviewer']['id'], self.coordinator.pk)
        pair.refresh_from_db()
        self.assertEqual(snapshot['reviewed_at'], pair.reviewed_at.isoformat())
        self.assertEqual(self.review(pair).status_code, 200)
        self.assertEqual(CaseAction.objects.count(), 2)
        response = self.client.get(f'/api/overlaps?decision=all&pair={pair.pk}').data['results'][0]
        self.assertEqual(response['review_snapshot'], snapshot)

    def test_legacy_evidence_is_not_upgraded_or_historically_fabricated(self):
        pair = self.pair({'scope': 'Legacy original evidence'}, decision='unrelated', reviewer=self.coordinator, reviewed_at=timezone.now())
        response = self.client.get(f'/api/overlaps?decision=all&pair={pair.pk}').data['results'][0]
        self.assertEqual(response['evidence'], pair.evidence); self.assertIsNone(response['review_snapshot'])
        self.assertEqual(self.review(pair).status_code, 200)
        snapshot = CaseAction.objects.first().changes['review_snapshot']
        self.assertEqual(snapshot['evidence'], pair.evidence)
        self.assertIsNone(snapshot['matching_policy_revision'])

    def test_history_failure_rolls_back_pair_and_first_snapshot(self):
        pair = self.pair(); original = CaseAction.objects.create; calls = []
        def fail_second(**kwargs):
            calls.append(kwargs)
            if len(calls) == 2:
                raise RuntimeError('Second history insert failed')
            return original(**kwargs)
        with patch('cases.relationships.CaseAction.objects.create', side_effect=fail_second), self.assertRaises(RuntimeError):
            self.review(pair)
        pair.refresh_from_db()
        self.assertEqual(pair.decision, 'pending'); self.assertEqual(pair.version, 1)
        self.assertFalse(CaseAction.objects.exists())

    def test_manual_path_has_versioned_unscored_evidence_and_snapshots(self):
        response = self.client.post('/api/relationships', {'left': str(self.left.pk), 'right': str(self.right.pk),
            'decision': 'same_incident', 'reason': 'Manual independent review'}, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertIsNone(response.data['score']); self.assertEqual(response.data['origin'], 'manual')
        self.assertEqual(response.data['evidence']['discovery_method'], 'manual_selection')
        self.assertIsNotNone(response.data['review_snapshot']); self.assertEqual(CaseAction.objects.count(), 2)

    def test_snapshot_redaction_covers_case_institution_movements_and_csv(self):
        pair = self.pair(); self.review(pair)
        own = self.left if self.left.bureau_id == self.rb.pk else self.right
        for user in [self.officer, self.auditor]:
            self.client.force_authenticate(user)
            self.assertEqual(self.review(pair).status_code, 403)
        self.client.force_authenticate(self.officer)
        self.assertEqual(self.client.get('/api/overlaps').status_code, 403)
        for url in [f'/api/cases/{own.pk}', f'/api/institutions/{self.institution.pk}/history', '/api/movements']:
            payload = json.dumps(self.client.get(url).data, default=str)
            self.assertNotIn('review_snapshot', payload); self.assertNotIn('Restricted cross-Bureau evidence', payload)
        exported = b''.join(self.client.get('/api/movements.csv').streaming_content).decode()
        self.assertNotIn('review_snapshot', exported); self.assertNotIn('Restricted cross-Bureau evidence', exported)
        Membership.objects.filter(user=self.officer).update(bureau=self.pg)
        self.assertEqual(self.client.get(f'/api/cases/{own.pk}').status_code, 404)
        Membership.objects.filter(user=self.coordinator).update(role='officer', bureau=self.rb)
        self.client.force_authenticate(self.coordinator)
        self.assertEqual(self.client.get('/api/overlaps').status_code, 403)
        self.assertEqual(self.review(pair).status_code, 403)

    @patch('cases.matching.runtime', return_value=('unused', 'encoder', .75))
    def test_pgvector_candidates_unchanged_and_reviewed_evidence_survives_reruns(self, _runtime):
        from pgvector.django import CosineDistance
        vector = [1.] + [0.] * 383
        Complaint.objects.filter(pk=self.right.pk).update(embedding=vector, model_revision='encoder', status='disposed')
        for i in range(6):
            case = self.make_case(f'N{i}', self.rb)
            x = .99 - .02 * i
            Complaint.objects.filter(pk=case.pk).update(embedding=[x, (1-x*x)**.5] + [0.] * 382, model_revision='encoder')
        foreign = self.make_case('FOREIGN', self.rb)
        other = Institution.objects.create(name='Other', permanent_id='OTHER-EVIDENCE')
        Complaint.objects.filter(pk=foreign.pk).update(institution=other, embedding=vector, model_revision='encoder')
        old = list(Complaint.objects.filter(institution=self.institution, embedding__isnull=False, model_revision='encoder').exclude(pk=self.left.pk)
            .annotate(distance=CosineDistance('embedding', vector)).order_by('distance')[:5])
        expected = {c.pk for c in old if 1-float(c.distance) >= .75}
        match_case(str(self.left.pk), vector=vector, encoded_revision='encoder')
        candidates = list(OverlapCandidate.objects.filter(left=self.left) | OverlapCandidate.objects.filter(right=self.left))
        actual = {p.right_id if p.left_id == self.left.pk else p.left_id for p in candidates}
        self.assertEqual(actual, expected); self.assertEqual(len(actual), 5); self.assertIn(self.right.pk, actual)
        pair = OverlapCandidate.objects.get(left=self.left, right=self.right)
        self.assertEqual(pair.evidence['schema_version'], 1)
        self.review(pair); pair.refresh_from_db(); saved = deepcopy(pair.evidence)
        actions = list(CaseAction.objects.values_list('changes', flat=True))
        match_case(str(self.left.pk), vector=vector, encoded_revision='encoder')
        pair.refresh_from_db()
        self.assertEqual(pair.evidence, saved); self.assertEqual(pair.decision, 'related_issue')
        self.assertEqual(list(CaseAction.objects.values_list('changes', flat=True)), actions)

    @patch('cases.matching.runtime', return_value=('unused', 'encoder', .75))
    def test_changed_pending_evidence_advances_version_and_stale_review_conflicts(self, _runtime):
        vector = [1.] + [0.] * 383
        Complaint.objects.filter(pk=self.right.pk).update(embedding=vector, model_revision='encoder')
        pair = self.pair({'scope': 'Legacy pending'})
        match_case(str(self.left.pk), vector=vector, encoded_revision='encoder')
        self.assertEqual(self.review(pair).status_code, 409)
        pair.refresh_from_db(); self.assertEqual(pair.version, 2)
        match_case(str(self.left.pk), vector=vector, encoded_revision='encoder')
        pair.refresh_from_db(); self.assertEqual(pair.version, 2)


class ConcurrentEvidenceTests(EvidenceFixture, TransactionTestCase):
    def test_two_real_concurrent_reviews_have_one_winner_and_two_consistent_snapshots(self):
        pair = self.pair()
        def request(reason):
            close_old_connections()
            try:
                client = APIClient(); client.force_authenticate(self.coordinator)
                return client.post(f'/api/overlaps/{pair.pk}/review', {'decision': 'related_issue', 'reason': reason, 'expected_version': 1}, format='json').status_code
            finally:
                close_old_connections()
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(request, ['First independent reason', 'Second independent reason']))
        self.assertEqual(sorted(results), [200, 409])
        snapshots = list(CaseAction.objects.values_list('changes__review_snapshot', flat=True))
        self.assertEqual(len(snapshots), 2); self.assertEqual(snapshots[0], snapshots[1])


def corpus_fixture():
    records = [dict(id=key, family=family, split=split, institution='TEST', text=text) for key, family, split, text in [
        ('cal', 1, 'calibration', 'Calibration text'), ('query', 2, 'test', 'Query text'),
        ('reference', 2, 'test', 'Reference text'), ('unjudged', 3, 'test', 'Unjudged text')]]
    return {'records': records, 'pairs': [{'left': 'query', 'right': 'reference', 'split': 'test', 'label': 'same_incident'}],
        'retrieval': [{'query': 'query', 'relevant': ['reference'], 'split': 'test'}], 'label_provenance': 'Synthetic test'}


class EvaluationSafetyTests(SimpleTestCase):
    def model(self):
        return SimpleNamespace(encode=lambda texts, **kwargs: np.array([[1.] + [0.] * 383 for _ in texts]))

    def test_query_ids_are_excluded_without_suffixes_and_unjudged_is_not_negative(self):
        report = evaluate(corpus_fixture(), self.model(), .75)
        result = report['retrieval']
        self.assertEqual(result['queries'][0]['eligible_candidates'], 2)
        self.assertEqual(result['same_incident_recall_at_5'], 1.)
        self.assertEqual(result['judged_suggestions'], 1); self.assertEqual(result['unjudged_suggestions'], 1)
        self.assertIsNone(result['overall_suggestion_precision'])
        self.assertEqual(result['review_worthy_precision_on_judged_suggestions'], 1.)

    def test_invalid_records_duplicates_and_family_leakage_are_reported_or_rejected(self):
        corpus = corpus_fixture(); corpus['records'].append({'id': 'missing'})
        self.assertEqual(len(eligible_corpus(corpus)[3]['invalid_records']), 1)
        corpus = corpus_fixture(); corpus['records'][1]['family'] = 1
        with self.assertRaises(CommandError): eligible_corpus(corpus)
        corpus = corpus_fixture(); corpus['records'].append(corpus['records'][0])
        with self.assertRaises(CommandError): eligible_corpus(corpus)
        corpus = corpus_fixture(); corpus['records'][3]['text'] = ' Calibration TEXT '
        report = eligible_corpus(corpus)[3]
        self.assertEqual(report['excluded_repeated_test_ids'], ['unjudged'])

    def test_unavailable_vectors_are_reported_as_abstentions_and_misses(self):
        model = self.model()
        def encode(texts, **kwargs):
            values = np.ones((len(texts), 384))
            values[texts.index('Query text')] = np.nan
            return values
        model.encode = encode
        report = evaluate(corpus_fixture(), model, .75)['retrieval']
        self.assertEqual(report['embedding_abstentions'], 1)
        self.assertEqual(report['same_incident_recall_at_5'], 0.)
        self.assertIn('query', report['unavailable_embedding_ids'])

    def test_default_evaluation_cannot_modify_calibration_or_reuse_outputs(self):
        calibration = settings.BASE_DIR / 'calibration.json'
        original = calibration.read_bytes()
        with TemporaryDirectory() as directory, override_settings(RESULTS_DIR=Path(directory)):
            data = Path(directory) / 'fixture.json'; data.write_text(json.dumps(corpus_fixture()))
            with patch('cases.management.commands.evaluate_matching.encoder', return_value=self.model()), patch('cases.management.commands.evaluate_matching.runtime', return_value=('model', 'pinned', .603)):
                call_command('evaluate_matching', data=str(data), stdout=io.StringIO())
                outputs = list((Path(directory) / 'runs').glob('*/matching.json'))
                self.assertEqual(len(outputs), 1)
                output = json.loads(outputs[0].read_text())
                self.assertEqual(output['threshold'], .603)
                self.assertEqual(output['matching_policy_revision'], MATCHING_POLICY_REVISION)
                self.assertNotIn('models', output)
                for forbidden in [calibration, data, outputs[0]]:
                    with self.assertRaises(CommandError):
                        call_command('evaluate_matching', data=str(data), output=str(forbidden), stdout=io.StringIO())
        self.assertEqual(calibration.read_bytes(), original)

    def test_active_model_switch_aborts_without_publishing_a_misidentified_report(self):
        with TemporaryDirectory() as directory, override_settings(RESULTS_DIR=Path(directory)):
            data = Path(directory) / 'fixture.json'; data.write_text(json.dumps(corpus_fixture()))
            with patch('cases.management.commands.evaluate_matching.encoder', return_value=self.model()), patch(
                    'cases.management.commands.evaluate_matching.runtime', side_effect=[('a', 'one', .6), ('b', 'two', .6)]):
                with self.assertRaisesMessage(CommandError, 'Active model changed'):
                    call_command('evaluate_matching', data=str(data), stdout=io.StringIO())
            self.assertFalse(list(Path(directory).glob('runs/**/*.json')))
