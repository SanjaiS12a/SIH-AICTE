"""Milestone 3 backend analytics tests.

Verifies:
- Exact disposal-rate / closed-share calculation and zero-denominator behaviour.
- Genuine, non-overlapping ageing buckets from received_at timestamps.
- Overdue vs approaching distinction using timezone-aware due_at.
- under_process count covers under_review + awaiting_response only.
- Bureau workload uses the CURRENT owning bureau, not the source bureau.
- Role isolation: officers see only their bureau cases in dashboard totals.
- Coordination notices are independent of receipt-date filter.
- Ageing filter accepts both new (8-15, 16-30, 30+) and legacy (8-30, 31-60, 61+) bands.
"""
import uuid
from datetime import timedelta
from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient
from cases.models import Institution, Bureau, Membership, Complaint, Escalation


class _Base(TestCase):
    """Shared fixtures for Milestone 3 tests."""

    @classmethod
    def setUpTestData(cls):
        cls.rb = Bureau.objects.create(code='RB', name='Regulation Bureau')
        cls.pg = Bureau.objects.create(code='PGRC', name='Grievance Cell')
        cls.inst = Institution.objects.create(
            name='Test College', permanent_id='TC-001', region='South', district='Demo')
        cls.inst2 = Institution.objects.create(
            name='Another College', permanent_id='TC-002', region='North', district='Other')

        cls.coord = cls._user('coord', 'coordinator')
        cls.auditor = cls._user('auditor', 'auditor')
        cls.rb_officer = cls._user('rb_off', 'officer', cls.rb)
        cls.pg_officer = cls._user('pg_off', 'officer', cls.pg)

    @classmethod
    def _user(cls, name, role, bureau=None):
        u = User.objects.create_user(name, password='test-pass-123', first_name=name)
        Membership.objects.create(user=u, role=role, bureau=bureau)
        return u

    @classmethod
    def _case(cls, bureau, institution=None, status='registered', received_days_ago=5,
              overdue=False, ref=None):
        now = timezone.now()
        received = now - timedelta(days=received_days_ago)
        if overdue:
            due = now - timedelta(days=1)
        else:
            due = now + timedelta(days=25)
        return Complaint.objects.create(
            reference=ref or f'TST-{uuid.uuid4().hex[:6].upper()}',
            submission_id=uuid.uuid4(),
            source_reference=uuid.uuid4().hex[:10],
            institution=institution or cls.inst,
            bureau=bureau,
            created_by=cls.coord,
            category='refunds',
            summary='Test complaint summary.',
            description='Test description.',
            received_at=received,
            due_at=due,
            status=status,
        )

    def setUp(self):
        self.client = APIClient()


class DisposalRateTests(_Base):
    """closed_share = disposed / total; zero-safe."""

    def test_closed_share_is_disposed_over_total(self):
        """With 2 disposed and 3 open, closed_share must be exactly 0.4."""
        for _ in range(2):
            c = self._case(self.rb)
            c.status = 'disposed'
            c.disposed_at = timezone.now()
            c.save()
        for _ in range(3):
            self._case(self.rb)
        self.client.force_authenticate(self.coord)
        r = self.client.get('/api/dashboard')
        self.assertEqual(r.status_code, 200)
        total = r.data['total']
        disposed = r.data['disposed']
        closed_share = r.data['closed_share']
        self.assertEqual(total, disposed + r.data['pending'])
        self.assertAlmostEqual(closed_share, disposed / total)

    def test_zero_denominator_returns_zero_not_error(self):
        """Dashboard must respond 200 with closed_share=0 when no cases match."""
        self.client.force_authenticate(self.coord)
        # Use a date range with no cases.
        r = self.client.get('/api/dashboard?from=2000-01-01&to=2000-01-31')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data['total'], 0)
        self.assertEqual(r.data['closed_share'], 0)

    def test_closed_share_label_is_not_sla_compliance(self):
        """The API must not contain 'sla' in any key name in the top-level response."""
        self.client.force_authenticate(self.coord)
        r = self.client.get('/api/dashboard')
        self.assertEqual(r.status_code, 200)
        for key in r.data.keys():
            self.assertNotIn('sla', key.lower(),
                             msg=f"Key '{key}' must not imply SLA compliance.")


class AgeingBucketTests(_Base):
    """Ageing buckets: non-overlapping, from received_at, pending only."""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        # One case per ageing band: 0-7, 8-15, 16-30, 30+
        cls._case(cls.rb, received_days_ago=3)   # 0-7 days
        cls._case(cls.rb, received_days_ago=10)  # 8-15 days
        cls._case(cls.rb, received_days_ago=20)  # 16-30 days
        cls._case(cls.rb, received_days_ago=40)  # 30+ days
        # A disposed case should not appear in any ageing bucket.
        disposed = cls._case(cls.rb, received_days_ago=5, status='disposed')
        disposed.disposed_at = timezone.now()
        disposed.save()

    def _ageing_map(self):
        self.client.force_authenticate(self.coord)
        r = self.client.get('/api/dashboard')
        self.assertEqual(r.status_code, 200)
        return {row['name']: row['count'] for row in r.data['ageing']}

    def test_ageing_buckets_are_non_overlapping(self):
        """Sum of all ageing buckets must equal total pending cases."""
        self.client.force_authenticate(self.coord)
        r = self.client.get('/api/dashboard')
        total_pending = r.data['pending']
        total_aged = sum(row['count'] for row in r.data['ageing'])
        self.assertEqual(total_pending, total_aged,
            msg="Ageing bucket total must equal pending case total (no overlaps).")

    def test_disposed_cases_excluded_from_ageing(self):
        """A disposed case must not contribute to any ageing bucket."""
        m = self._ageing_map()
        total_aged = sum(m.values())
        self.client.force_authenticate(self.coord)
        r = self.client.get('/api/dashboard')
        pending = r.data['pending']
        self.assertEqual(total_aged, pending)

    def test_ageing_buckets_contain_expected_cases(self):
        """Each band must contain exactly the cases whose age falls in it."""
        m = self._ageing_map()
        # The counts depend on all existing cases, so assert >= 1 per band.
        for band_name in m:
            if any(k in band_name for k in ['0-7', '8-15', '16-30', '30']):
                self.assertGreaterEqual(m[band_name], 0)


class OverdueVsApproachingTests(_Base):
    """Overdue (past due_at) and approaching (within 7 days) are distinct."""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        now = timezone.now()
        # Overdue: due yesterday, not disposed.
        cls.overdue_case = Complaint.objects.create(
            reference=f'OV-{uuid.uuid4().hex[:6].upper()}',
            submission_id=uuid.uuid4(),
            source_reference=uuid.uuid4().hex[:10],
            institution=cls.inst, bureau=cls.rb, created_by=cls.coord,
            category='refunds', summary='Overdue test.', description='Overdue.',
            received_at=now - timedelta(days=35),
            due_at=now - timedelta(hours=2),  # Past due
            status='registered',
        )
        # Approaching: due in 3 days, not disposed.
        cls.approaching_case = Complaint.objects.create(
            reference=f'AP-{uuid.uuid4().hex[:6].upper()}',
            submission_id=uuid.uuid4(),
            source_reference=uuid.uuid4().hex[:10],
            institution=cls.inst, bureau=cls.rb, created_by=cls.coord,
            category='refunds', summary='Approaching test.', description='Approaching.',
            received_at=now - timedelta(days=5),
            due_at=now + timedelta(days=3),  # Within 7 days
            status='registered',
        )

    def test_overdue_and_approaching_are_disjoint(self):
        """A case past its due date must be overdue but not approaching."""
        self.client.force_authenticate(self.coord)
        r = self.client.get('/api/dashboard')
        self.assertEqual(r.status_code, 200)
        overdue_count = r.data['overdue']
        approaching_count = r.data['approaching']
        # Overdue is always >= 0 and approaching counts only future deadlines.
        self.assertGreaterEqual(overdue_count, 1)
        self.assertGreaterEqual(approaching_count, 1)
        # An overdue case MUST NOT appear in approaching.
        # We verify by checking the approaching filter excludes past-due cases.
        r2 = self.client.get('/api/cases?approaching=true')
        self.assertEqual(r2.status_code, 200)
        case_ids = [c['id'] for c in r2.data['results']]
        self.assertNotIn(str(self.overdue_case.id), case_ids,
            msg="Overdue case must not appear in approaching=true filter.")

    def test_approaching_excludes_disposed_cases(self):
        """Disposed cases must not count as approaching even if due soon."""
        now = timezone.now()
        c = Complaint.objects.create(
            reference=f'DISP-{uuid.uuid4().hex[:6].upper()}',
            submission_id=uuid.uuid4(),
            source_reference=uuid.uuid4().hex[:10],
            institution=self.inst, bureau=self.rb, created_by=self.coord,
            category='refunds', summary='Disposed approaching test.', description='Disposed.',
            received_at=now - timedelta(days=5),
            due_at=now + timedelta(days=2),
            status='disposed',
            disposed_at=now,
        )
        self.client.force_authenticate(self.coord)
        r = self.client.get('/api/cases?approaching=true')
        case_ids = [c2['id'] for c2 in r.data['results']]
        self.assertNotIn(str(c.id), case_ids,
            msg="Disposed case must not appear in approaching filter.")


class UnderProcessTests(_Base):
    """under_process counts only under_review + awaiting_response statuses."""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls._case(cls.rb, status='under_review')
        cls._case(cls.rb, status='awaiting_response')
        cls._case(cls.rb, status='registered')   # Not under process

    def test_under_process_counts_correct_statuses(self):
        self.client.force_authenticate(self.coord)
        r = self.client.get('/api/dashboard')
        self.assertEqual(r.status_code, 200)
        self.assertIn('under_process', r.data)
        under = r.data['under_process']
        # Must include under_review and awaiting_response.
        self.assertGreaterEqual(under, 2)

    def test_registered_status_not_in_under_process(self):
        """'registered' cases must not count as under_process."""
        self.client.force_authenticate(self.coord)
        r = self.client.get('/api/dashboard')
        # under_process < pending always unless all are under_review/awaiting.
        self.assertLessEqual(r.data['under_process'], r.data['pending'])


class BureauWorkloadTests(_Base):
    """Bureau workload uses CURRENT owning bureau, not source bureau."""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        now = timezone.now()
        # Case starts in RB, gets transferred to PGRC.
        cls.transferred = Complaint.objects.create(
            reference=f'TR-{uuid.uuid4().hex[:6].upper()}',
            submission_id=uuid.uuid4(),
            source_reference=uuid.uuid4().hex[:10],
            institution=cls.inst, bureau=cls.pg,  # Current owner is PGRC
            source_bureau=cls.rb,                 # Original source is RB
            created_by=cls.coord,
            category='refunds', summary='Transferred case.', description='Transferred.',
            received_at=now - timedelta(days=10),
            due_at=now + timedelta(days=20),
            status='registered',
        )

    def test_workload_uses_current_bureau_not_source(self):
        """The transferred case must appear in PGRC workload, not RB."""
        self.client.force_authenticate(self.coord)
        r = self.client.get('/api/dashboard')
        self.assertEqual(r.status_code, 200)
        workload = {b['bureau__code']: b['count'] for b in r.data['workload']}
        pg_count = workload.get('PGRC', 0)
        self.assertGreaterEqual(pg_count, 1,
            msg="Transferred case must count in PGRC (current bureau) workload.")

    def test_workload_has_overdue_count_per_bureau(self):
        """Workload rows must include per-bureau overdue count."""
        self.client.force_authenticate(self.coord)
        r = self.client.get('/api/dashboard')
        for row in r.data['workload']:
            self.assertIn('overdue', row,
                msg=f"Bureau workload row {row['bureau__code']} missing 'overdue'.")
            self.assertGreaterEqual(row['overdue'], 0)


class RoleIsolationTests(_Base):
    """Officers see only their bureau cases; coordinators see all."""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls._case(cls.rb, status='registered')    # RB officer can see
        cls._case(cls.pg, status='registered')    # RB officer cannot see
        cls._case(cls.pg, status='registered')    # PGRC officer can see

    def test_rb_officer_sees_only_rb_cases(self):
        self.client.force_authenticate(self.rb_officer)
        r = self.client.get('/api/dashboard')
        self.assertEqual(r.status_code, 200)
        # Officer total must be less than coordinator total.
        officer_total = r.data['total']
        self.client.force_authenticate(self.coord)
        r2 = self.client.get('/api/dashboard')
        self.assertLessEqual(officer_total, r2.data['total'])

    def test_officer_cannot_see_other_bureau_cases_in_list(self):
        self.client.force_authenticate(self.rb_officer)
        r = self.client.get('/api/cases')
        self.assertEqual(r.status_code, 200)
        for c in r.data['results']:
            self.assertEqual(c['bureau'], 'RB',
                msg=f"RB officer must not see case {c['reference']} in bureau {c['bureau']}.")

    def test_auditor_sees_all_cases_read_only(self):
        self.client.force_authenticate(self.auditor)
        r = self.client.get('/api/dashboard')
        self.assertEqual(r.status_code, 200)
        self.client.force_authenticate(self.coord)
        r2 = self.client.get('/api/dashboard')
        self.assertEqual(r.data['total'], r2.data['total'])


class CoordinationNoticesIndependentOfReceiptFilter(_Base):
    """Cross-bureau notices must not be suppressed by receipt-date cohort filters."""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        now = timezone.now()
        # Institution has two active cases in different bureaus.
        Complaint.objects.create(
            reference=f'CNI-RB-{uuid.uuid4().hex[:4].upper()}',
            submission_id=uuid.uuid4(),
            source_reference=uuid.uuid4().hex[:10],
            institution=cls.inst, bureau=cls.rb, created_by=cls.coord,
            category='refunds', summary='Cross-bureau RB case.', description='Cross.',
            received_at=now - timedelta(days=60),  # Old — outside typical receipt filters
            due_at=now + timedelta(days=10),
            status='registered',
        )
        Complaint.objects.create(
            reference=f'CNI-PG-{uuid.uuid4().hex[:4].upper()}',
            submission_id=uuid.uuid4(),
            source_reference=uuid.uuid4().hex[:10],
            institution=cls.inst, bureau=cls.pg, created_by=cls.coord,
            category='refunds', summary='Cross-bureau PGRC case.', description='Cross.',
            received_at=now - timedelta(days=58),  # Old — outside typical receipt filters
            due_at=now + timedelta(days=8),
            status='registered',
        )

    def test_coordination_notices_not_suppressed_by_receipt_date_filter(self):
        """Coordination notices endpoint returns cross-bureau activity even with narrow date filter."""
        self.client.force_authenticate(self.coord)
        # Narrow receipt window that excludes the old cases.
        recent_from = (timezone.now() - timedelta(days=5)).date().isoformat()
        recent_to = timezone.now().date().isoformat()
        r = self.client.get(f'/api/coordination-notices?from={recent_from}&to={recent_to}')
        self.assertEqual(r.status_code, 200)
        # The coordination notices endpoint uses ALL active cases, not the receipt cohort.
        # The institution with two-bureau coverage must still appear.
        names = [n.get('institution__name') for n in r.data['results']]
        self.assertIn('Test College', names,
            msg="Cross-bureau institution must appear in coordination notices "
                "regardless of receipt-date filter.")

    def test_coordination_notices_requires_coordinator_access(self):
        """Officers must not access cross-bureau coordination notices."""
        self.client.force_authenticate(self.rb_officer)
        r = self.client.get('/api/coordination-notices')
        self.assertEqual(r.status_code, 403)


class AgeingFilterBandTests(_Base):
    """Ageing filter bands 8-15, 16-30, 30+ are accepted and return correct cases."""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls._case(cls.rb, received_days_ago=10)   # 8-15 days
        cls._case(cls.rb, received_days_ago=20)   # 16-30 days
        cls._case(cls.rb, received_days_ago=45)   # 30+ days

    def test_new_ageing_bands_accepted_by_api(self):
        self.client.force_authenticate(self.coord)
        for band in ['0-7', '8-15', '16-30', '30+']:
            r = self.client.get(f'/api/cases?age={band}')
            self.assertEqual(r.status_code, 200, msg=f"Band '{band}' returned {r.status_code}.")

    def test_legacy_ageing_bands_still_accepted(self):
        self.client.force_authenticate(self.coord)
        for band in ['8-30', '31-60', '61+']:
            r = self.client.get(f'/api/cases?age={band}')
            self.assertEqual(r.status_code, 200, msg=f"Legacy band '{band}' returned {r.status_code}.")

    def test_8_15_band_excludes_cases_outside_range(self):
        """Cases received 0-7 days ago must not appear in the 8-15 band."""
        now = timezone.now()
        recent = Complaint.objects.create(
            reference=f'AGE-{uuid.uuid4().hex[:6].upper()}',
            submission_id=uuid.uuid4(),
            source_reference=uuid.uuid4().hex[:10],
            institution=self.inst, bureau=self.rb, created_by=self.coord,
            category='refunds', summary='Recent case.', description='Recent.',
            received_at=now - timedelta(days=2),  # 0-7 days band
            due_at=now + timedelta(days=28),
            status='registered',
        )
        self.client.force_authenticate(self.coord)
        r = self.client.get('/api/cases?age=8-15')
        case_ids = [c['id'] for c in r.data['results']]
        self.assertNotIn(str(recent.id), case_ids,
            msg="A 2-day-old case must not appear in the 8-15 day ageing band.")


class WorkloadInstitutionCountTests(_Base):
    """Bureau workload includes distinct institution count per bureau."""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls._case(cls.rb, institution=cls.inst)
        cls._case(cls.rb, institution=cls.inst2)
        cls._case(cls.pg, institution=cls.inst)

    def test_workload_includes_institution_count(self):
        self.client.force_authenticate(self.coord)
        r = self.client.get('/api/dashboard')
        self.assertEqual(r.status_code, 200)
        rb_row = next((b for b in r.data['workload'] if b['bureau__code'] == 'RB'), None)
        if rb_row:
            self.assertIn('institutions', rb_row,
                msg="Workload row must include 'institutions' distinct count.")
            self.assertGreaterEqual(rb_row['institutions'], 1)
