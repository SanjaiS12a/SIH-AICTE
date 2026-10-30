"""Collect published education-finance complaint context, never manufacture incident labels."""
import csv
import hashlib
import io
import json
from pathlib import Path
import urllib.request
import zipfile

from audit_indian_complaints import redact

ROOT = Path(__file__).resolve().parents[1]
URL = 'https://files.consumerfinance.gov/f/documents/CCDB_Export_9_January_2025_through_February_2025.zip'


def main():
    directory = ROOT / 'data/research/complaint_context'
    directory.mkdir(parents=True, exist_ok=True)
    archive = directory / 'CFPB-Jan-Feb-2025.zip'
    if not archive.exists():
        with urllib.request.urlopen(URL, timeout=120) as response:
            content = response.read(100 * 1024 * 1024 + 1)
        if len(content) > 100 * 1024 * 1024:
            raise ValueError('Archive exceeds the collection limit')
        archive.write_bytes(content)
    total = selected = empty = duplicates = 0
    seen, records = set(), []
    with zipfile.ZipFile(archive) as book:
        if sum(info.file_size for info in book.infolist()) > 600 * 1024 * 1024:
            raise ValueError('Expanded archive exceeds limit')
        for name in book.namelist():
            if not name.lower().endswith('.csv'):
                continue
            with book.open(name) as binary:
                rows = csv.DictReader(io.TextIOWrapper(binary, encoding='utf-8-sig', newline=''))
                for row in rows:
                    total += 1
                    product = row.get('Product', '')
                    if 'student loan' not in product.casefold():
                        continue
                    selected += 1
                    text = row.get('Consumer complaint narrative', '').strip()
                    if not text:
                        empty += 1
                        continue
                    text = redact(text)
                    digest = hashlib.sha256(text.encode()).hexdigest()
                    if digest in seen:
                        duplicates += 1
                        continue
                    seen.add(digest)
                    records.append({'id': digest, 'text': text, 'product': product, 'issue': row.get('Issue', ''),
                                    'source': URL, 'overlap_label': None,
                                    'provenance': 'CFPB published student-loan complaint narrative; financial context, not an AICTE case'})
    destination = directory / 'student-loan-context.jsonl'
    destination.write_text(''.join(json.dumps(record, ensure_ascii=False) + '\n' for record in records), encoding='utf-8')
    report = {'source': 'CFPB Consumer Complaint Narratives Archive, January-February 2025', 'url': URL,
              'publisher_policy': 'https://www.consumerfinance.gov/data-research/consumer-complaints/',
              'archive_sha256': hashlib.sha256(archive.read_bytes()).hexdigest(), 'archive_bytes': archive.stat().st_size,
              'total_rows': total, 'student_loan_rows': selected, 'missing_narrative': empty,
              'duplicate_narratives': duplicates, 'retained_records': len(records),
              'derived_sha256': hashlib.sha256(destination.read_bytes()).hexdigest(),
              'access': 'Official public archive; publisher describes public complaint data as freely available for use, analysis and building on',
              'labels': 'Issue/product classifications, not same-incident or related-issue pairs',
              'training_use': 'Excluded from supervised overlap/paraphrase training; context/review material only',
              'privacy': 'Derived file omits complaint IDs, locations and company metadata and applies identifier masking. This is pseudonymization, not a guarantee that names/context are anonymous; manual review remains required.',
              'domain_limit': 'Student lending, not AICTE institutional complaints. Do not resolve companies to institutions or fabricate relationship labels.'}
    (ROOT / 'tests/results/complaint-context-2025-audit.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
