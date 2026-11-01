"""Collect minimal public fields into a new private, ignored research workspace."""
import argparse
import hashlib
import json
import re
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

CFPB = 'https://www.consumerfinance.gov/data-research/consumer-complaints/search/api/v1/'
NYC = 'https://data.cityofnewyork.us/resource/erm2-nwe9.json'
LABELS = {'same_incident', 'related_issue', 'unrelated', 'insufficient_evidence'}


def digest(value):
    return hashlib.sha256(value).hexdigest()


def write_new(path, value):
    path = Path(path)
    with path.open('x', encoding='utf-8') as target:
        json.dump(value, target, ensure_ascii=False, indent=2, allow_nan=False)


def fetch(url, limit=12_000_000):
    request = urllib.request.Request(url, headers={'User-Agent': 'SIH26264-Research/1.0 (bounded public-data research)'})
    with urllib.request.urlopen(request, timeout=30) as response:
        data = response.read(limit + 1)
        if len(data) > limit:
            raise ValueError('Source response exceeded bounded collection size.')
        return data, {'url': response.geturl(), 'etag': response.headers.get('ETag'),
                      'last_modified': response.headers.get('Last-Modified'), 'sha256': digest(data)}


def redact(text):
    """Conservative automatic masking is not certification of de-identification."""
    changes = []
    patterns = [('email', r'\b[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}\b'),
                ('url', r'https?://\S+'),
                ('phone_or_long_identifier', r'(?<!\w)(?:\+?\d[\d ()-]{7,}\d)(?!\w)'),
                ('street_address', r'\b\d{1,6}\s+(?:[A-Za-z]+\s+){0,4}(?:Street|St|Road|Rd|Avenue|Ave|Lane|Ln|Drive|Dr|Boulevard|Blvd)\b')]
    for name, pattern in patterns:
        text, count = re.subn(pattern, '[REDACTED]', text, flags=re.I)
        if count:
            changes.append({'kind': name, 'count': count})
    return text, changes


def source_manifest(dataset, url, terms_url, conditions):
    return {'dataset': dataset, 'source_url': url, 'terms_url': terms_url, 'usage_conditions': conditions,
            'collected_at_utc': datetime.now(timezone.utc).isoformat(), 'source_version': 'Collection-time snapshot; see response metadata/checksum',
            'evaluation_permitted': False, 'redistribution_allowed': False, 'status': 'pending', 'records': 0}


def normalize_cfpb(rows):
    records = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        identifier = row.get('complaint_id') or row.get('Complaint ID')
        narrative = row.get('complaint_what_happened') or row.get('Consumer complaint narrative')
        if not identifier or not isinstance(narrative, str) or not narrative.strip():
            continue
        company = row.get('company') or row.get('Company')
        cleaned, redactions = redact(narrative)
        records.append({'id': f'cfpb-{identifier}', 'dataset': 'cfpb', 'source_id': str(identifier),
            'source_url': f'https://www.consumerfinance.gov/data-research/consumer-complaints/search/detail/{identifier}',
            'original_text': narrative, 'model_text': cleaned, 'text_type': 'published_consumer_narrative',
            'publication_date': None, 'receipt_date': row.get('date_received') or row.get('Date received'),
            'category': row.get('product') or row.get('Product') or 'Not recorded',
            'entity': {'name': company, 'type': 'company', 'source_field': 'company'} if company else None,
            'institution_id': None, 'incident_group': None, 'independent_incident_labels': False,
            'privacy_status': 'provider-masked-plus-automatic-redaction; manual re-identification review pending',
            'redactions': redactions, 'eligible': bool(cleaned.strip()), 'eligibility_reason': 'Tokenizer eligibility checked at evaluation'})
    return records


def normalize_nyc(rows):
    records = []
    for row in rows:
        if not isinstance(row, dict) or not row.get('unique_key'):
            continue
        # These are structured descriptions, not original citizen narratives.
        selected = {key: row.get(key) for key in ['unique_key', 'created_date', 'closed_date', 'agency', 'complaint_type', 'descriptor', 'status']}
        text = ' — '.join(str(selected[key]) for key in ['complaint_type', 'descriptor'] if selected[key])
        records.append({'id': f'nyc-{row["unique_key"]}', 'dataset': 'nyc311', 'source_id': str(row['unique_key']),
            'source_url': 'https://data.cityofnewyork.us/d/erm2-nwe9', 'original_text': None, 'original_fields': selected,
            'model_text': text, 'text_type': 'structured_request_fields', 'publication_date': None,
            'receipt_date': selected['created_date'], 'category': selected['complaint_type'] or 'Not recorded',
            'entity': {'name': selected['agency'], 'type': 'agency', 'source_field': 'agency'} if selected['agency'] else None,
            'institution_id': None, 'incident_group': None, 'independent_incident_labels': False,
            'privacy_status': 'minimal public fields; addresses, geography and contact fields not collected', 'redactions': [],
            'eligible': bool(text.strip()), 'eligibility_reason': 'Structured workflow probe, not narrative or institution validation'})
    return records


def validate_manifest(manifest):
    if manifest.get('private_storage') is not True or not isinstance(manifest.get('sources'), list):
        raise ValueError('A private workspace and source/usage manifests are required.')
    for source in manifest['sources']:
        if not all(source.get(key) for key in ['dataset', 'source_url', 'terms_url', 'usage_conditions', 'collected_at_utc']):
            raise ValueError('Incomplete source provenance or usage conditions.')
        if source.get('status') == 'collected':
            response = source.get('response')
            if (source.get('evaluation_permitted') is not True or not isinstance(response,dict)
                    or not isinstance(response.get('sha256'),str) or not re.fullmatch('[a-fA-F0-9]{64}',response['sha256'])):
                raise ValueError('Collected text requires documented permitted use and a source checksum.')


def collect(workspace, count=500):
    if not 1 <= count <= 2000:
        raise ValueError('Collection is bounded to 1–2,000 records per accessible source.')
    root = Path(workspace).resolve(); root.mkdir(parents=True, mode=0o700, exist_ok=False)
    oia = source_manifest('oia', 'https://www.oiahe.org.uk/resources-and-publications/case-summaries/',
        'https://www.oiahe.org.uk/media/nl0nxlte/publication-of-case-summaries-and-public-interest-cases.pdf',
        'Public anonymization policy is not a verified corpus reuse grant. User requested collection remain pending; no case text collected.')
    oia['status'] = 'pending_permission'
    cfpb = source_manifest('cfpb', CFPB, 'https://www.consumerfinance.gov/data-research/consumer-complaints/',
        'Publisher permits public complaint data use/analysis. Public narratives remain unverified allegations; no redistribution in this project. No restricted records or credentials.')
    cfpb['evaluation_permitted'] = True
    nyc = source_manifest('nyc311', NYC, 'https://a860-gpp.nyc.gov/downloads/5712m8144?locale=en',
        'NYC Open Data public-use policy and NYC.gov terms apply; source/version/modifications attributed. Informational data, no accuracy warranty; no personal location/contact fields collected.')
    nyc['evaluation_permitted'] = True
    records = []
    requests = [(cfpb, CFPB + '?' + urllib.parse.urlencode({'size': count, 'no_aggs': 'true', 'has_narrative': 'true', 'date_received_max': '2026-10-01'})),
        (nyc, NYC + '?' + urllib.parse.urlencode({'$limit': count, '$select': 'unique_key,created_date,closed_date,agency,complaint_type,descriptor,status'}))]
    for source, url in requests:
        try:
            raw, metadata = fetch(url)
            content = json.loads(raw)
            if source['dataset'] == 'cfpb':
                rows = [hit['_source'] for hit in content.get('hits', {}).get('hits', [])]
                normalized = normalize_cfpb(rows)
            else:
                rows = content; normalized = normalize_nyc(rows)
            # Raw storage contains only required selected fields, not the original HTTP envelope.
            write_new(root / (source['dataset'] + '-records.json'), normalized)
            source.update(status='collected', records=len(normalized), response=metadata,
                          raw_rows=len(rows), normalization='minimal fields; explicit derived-text/redaction provenance',
                          corpus_sha256=digest((root / (source['dataset'] + '-records.json')).read_bytes()))
            records.extend(normalized)
        except (urllib.error.URLError, TimeoutError, ValueError, KeyError) as exc:
            source.update(status='blocked', access_error=type(exc).__name__, http_status=getattr(exc, 'code', None))
    manifest = {'schema_version': 1, 'private_storage': True, 'redistribution_allowed': False,
                'sources': [oia, cfpb, nyc], 'institution_track': 'unavailable: no authorized independently labelled institution corpus supplied',
                'sampling': 'Bounded convenience snapshots, not representative sampling; no model/threshold tuning.'}
    write_new(root / 'corpus.json', records)
    manifest['corpus_sha256'] = digest((root/'corpus.json').read_bytes())
    validate_manifest(manifest)
    write_new(root / 'manifest.json', manifest)
    return manifest


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--workspace', required=True, help='New ignored private directory; configure Windows ACLs before collection.')
    parser.add_argument('--count', type=int, default=500)
    args = parser.parse_args()
    result = collect(args.workspace, args.count)
    print(json.dumps({s['dataset']: {'status': s['status'], 'records': s['records']} for s in result['sources']}))
