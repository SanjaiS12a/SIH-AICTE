"""Fictional records and evaluation labels; no real allegations or personal data."""
import random

TOPICS = {
    'admissions': [
        ('The college admitted students above its sanctioned intake in {year}.', 'Enrolment exceeded the approved seat capacity during the {year} admission cycle.'),
        ('Admission was refused despite a valid allotment letter in {year}.', 'A student holding an official seat allocation was denied enrolment for {year}.'),
        ('The college demanded an undeclared admission payment in {year}.', 'Applicants were asked for additional unlisted charges to secure admission in {year}.'),
    ],
    'refunds': [
        ('Tuition fees were not returned after an admission cancellation in {year}.', 'The institution has withheld the fee refund following withdrawal in {year}.'),
        ('The hostel security deposit remains unpaid after checkout in {year}.', 'After leaving the hostel in {year}, the resident has not received the caution deposit.'),
        ('An examination fee was charged twice and not reversed in {year}.', 'A duplicate exam payment made in {year} has not been reimbursed.'),
    ],
    'documents': [
        ('Original certificates were withheld after the student withdrew in {year}.', 'The institution refused to return original academic documents after withdrawal in {year}.'),
        ('The graduation transcript contains incorrect marks for {year}.', 'The academic record issued for {year} lists erroneous examination scores.'),
        ('A migration certificate requested in {year} has not been issued.', 'The college has delayed providing the transfer eligibility document requested in {year}.'),
    ],
    'facilities': [
        ('Drinking water in the hostel was unsafe during {year}.', 'Residents reported contaminated potable water in the hostel in {year}.'),
        ('The electrical engineering laboratory lacked working equipment in {year}.', 'Practical classes could not proceed because electrical lab instruments were broken in {year}.'),
        ('The library remained inaccessible to wheelchair users in {year}.', 'Wheelchair access to the campus library was unavailable throughout {year}.'),
    ],
    'scholarships': [
        ('The merit scholarship approved for {year} has not been disbursed.', 'Students have not received the sanctioned merit financial award for {year}.'),
        ('The institution did not forward a scholarship application in {year}.', 'A financial assistance request was not submitted to the funding authority in {year}.'),
        ('The scholarship payment went to an incorrect account in {year}.', 'Approved student financial support was credited to the wrong bank account in {year}.'),
    ],
    'administration': [
        ('Final semester results were delayed beyond the calendar in {year}.', 'Publication of the last semester examination outcome missed the academic schedule for {year}.'),
        ('An examination revaluation appeal received no response in {year}.', 'The request to review answer-script marks was left unanswered in {year}.'),
        ('The college did not publish its grievance committee details in {year}.', 'Information about the student complaint committee was absent from the website in {year}.'),
    ],
}

def evaluation_dataset():
    """Family-separated synthetic pairs; reference members remain available for retrieval."""
    rows, pairs, retrieval = [], [], []
    for family in range(100):
        category = list(TOPICS)[family % 6]
        topic = (family // 6) % 3
        year = 2023 + family // 36
        a, b = [x.format(year=year) for x in TOPICS[category][topic]]
        a += f' The matter concerns programme cohort {family + 1}.'
        b += f' This report concerns programme cohort {family + 1}.'
        negative = TOPICS[category][(topic + 1) % 3][0].format(year=year)
        related = TOPICS[category][topic][0].format(year=year-1) + f' This was a separate incident in the preceding year, cohort {family + 1}.'
        split = 'calibration' if family % 5 < 2 else 'test'
        institution = f'DEMO-{family % 30 + 1:04d}'
        rows.extend([{'id': f'{family}-a', 'family': family, 'split': split, 'institution': institution, 'text': a},
                     {'id': f'{family}-b', 'family': family, 'split': split, 'institution': institution, 'text': b},
                     {'id': f'{family}-n', 'family': family, 'split': split, 'institution': institution, 'text': negative},
                     {'id': f'{family}-r', 'family': family, 'split': split, 'institution': institution, 'text': related}])
        pairs.extend([{'left': f'{family}-a', 'right': f'{family}-b', 'label': 'same_incident', 'split': split, 'rationale': 'Same structured scenario, year and cohort; paraphrased allegation.'},
                      {'left': f'{family}-a', 'right': f'{family}-n', 'label': 'unrelated', 'split': split, 'rationale': 'Same institution and category, different alleged incident and requested remedy.'},
                      {'left': f'{family}-a', 'right': f'{family}-r', 'label': 'related_issue', 'split': split, 'rationale': 'Similar allegation at the same institution, explicitly a different year and incident. Review-worthy, not proof of duplicate.'}])
        retrieval.append({'query': f'{family}-b', 'relevant': [f'{family}-a'], 'split': split})
    return {'label_provenance': 'Authored synthetic scenario labels; independent human review pending.', 'records': rows, 'pairs': pairs, 'retrieval': retrieval}

def seed_records(count=500):
    rng = random.Random(26264)
    topics = [(cat, a, b) for cat, variants in TOPICS.items() for a, b in variants]
    records = []
    for n in range(count):
        family, variant = divmod(n, 5)
        category, a, b = topics[family % len(topics)]
        year = 2024 + family % 3
        summary = (a if variant % 2 == 0 else b).format(year=year)
        summary += f' The matter concerns programme cohort {family + 1}.'
        if variant == 4:
            category, a, _ = topics[(family + 7) % len(topics)]
            summary = a.format(year=year) + f' This is a separate incident, cohort {family + 1}.'
        age = rng.randrange(0, 115)
        disposed = n % 7 in (0, 1)
        records.append({'index': n, 'family': family, 'institution_index': family % 30,
                        'category': category, 'summary': summary, 'description': summary + '\n\nThis fictional complaint requests a documented review and a written response. Supporting facts should be checked by the responsible bureau. Synthetic demonstration record only.',
                        'year': year, 'age': age, 'status': 'disposed' if disposed else ['registered','under_review','awaiting_response'][n % 3]})
    return records
