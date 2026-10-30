"""Audited PAWS preparation; preserve published evaluation partitions and remove train leakage."""
import hashlib
import io
import json
import re
import unicodedata
from collections import Counter
from pathlib import Path
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data/research/public_pairs'
RESULTS = ROOT / 'tests/results'
FILES = {
    'final_train': ('labeled_final/train-00000-of-00001.parquet', '8dc9ad3e5f30ad9a86b290fe236d528ef23a5751fec9a35d99cbacf68ba277cf'),
    'dev': ('labeled_final/validation-00000-of-00001.parquet', '7760d829453764ba342a6f562809a8ed21c2c3eec3fd9ffa544089f145d42f6d'),
    'test': ('labeled_final/test-00000-of-00001.parquet', 'ae342ff12bb84b84b95f468abf5db6cb7c7bd578271299fe9c99be75b8132f4d'),
    'swap_train': ('labeled_swap/train-00000-of-00001.parquet', '21b9b68cd9398f01e6c766a9b12bc9a31cee11a6170a5acc5fa87ba853033a9b'),
}


def normalized(text):
    return re.sub(r'\s+', ' ', unicodedata.normalize('NFKC', text).casefold()).strip()


def download(url, destination, expected):
    if destination.exists() and hashlib.sha256(destination.read_bytes()).hexdigest() == expected:
        return destination.read_bytes()
    request = urllib.request.Request(url, headers={'User-Agent': 'AICTE-SIH-research/1.0'})
    with urllib.request.urlopen(request, timeout=120) as response:
        content = response.read(100 * 1024 * 1024 + 1)
    if len(content) > 100 * 1024 * 1024 or hashlib.sha256(content).hexdigest() != expected:
        raise ValueError('Download size or publisher checksum mismatch')
    destination.write_bytes(content)
    return content


def split_dev(rows):
    parent = {}

    def find(text):
        parent.setdefault(text, text)
        while parent[text] != text:
            parent[text] = parent[parent[text]]
            text = parent[text]
        return text

    for row in rows:
        a, b = sorted([find(normalized(row['sentence1'])), find(normalized(row['sentence2']))])
        parent[b] = a
    result = {'validation': [], 'calibration': []}
    for row in rows:
        component = find(normalized(row['sentence1']))
        key = 'validation' if int(hashlib.sha256(component.encode()).hexdigest(), 16) % 2 == 0 else 'calibration'
        result[key].append(row)
    assert not texts(result['validation']) & texts(result['calibration'])
    return result


def texts(rows):
    return {normalized(row[key]) for row in rows for key in ['sentence1', 'sentence2']}


def clean_training(rows, forbidden):
    accepted = {}
    conflicts = set()
    rejected = Counter()
    for row in rows:
        a, b = normalized(row['sentence1']), normalized(row['sentence2'])
        key = tuple(sorted([a, b]))
        if not a or not b or row['label'] not in (0, 1):
            raise ValueError('Malformed source pair')
        if a in forbidden or b in forbidden:
            rejected['heldout_sentence_overlap'] += 1
            continue
        if key in accepted:
            rejected['duplicate_pair'] += 1
            if accepted[key]['label'] != row['label']:
                conflicts.add(key)
            continue
        accepted[key] = row
    for key in conflicts:
        del accepted[key]
    rejected['conflicting_pair_groups_removed'] = len(conflicts)
    return list(accepted.values()), dict(rejected)


def main():
    import pyarrow.parquet as pq
    from tokenizers import Tokenizer
    DATA.mkdir(parents=True, exist_ok=True)
    sources, rows = [], {}
    for name, (remote, sha) in FILES.items():
        destination = DATA / (name + '.parquet')
        old = ROOT / 'data/research' / Path(remote).name
        if name != 'swap_train' and old.exists() and hashlib.sha256(old.read_bytes()).hexdigest() == sha:
            destination.write_bytes(old.read_bytes())
        url = 'https://huggingface.co/datasets/google-research-datasets/paws/resolve/main/' + remote
        content = download(url, destination, sha)
        rows[name] = pq.read_table(io.BytesIO(content)).to_pylist()
        for row in rows[name]:
            row['source'] = name
        sources.append({'name': name, 'url': url, 'sha256': sha, 'rows': len(rows[name]), 'labels': '1 paraphrase, 0 different meaning; NOT complaint incident labels'})
    assert [len(rows[k]) for k in FILES] == [49401, 8000, 8000, 30397]
    heldout = texts(rows['dev'] + rows['test'])
    train, rejected = clean_training(rows['final_train'] + rows['swap_train'], heldout)
    splits = {'train': train, **split_dev(rows['dev']), 'test': rows['test']}
    tokenizer = Tokenizer.from_file(str(ROOT / 'models/minilm/tokenizer.json'))
    tokenizer.no_truncation()
    tokenizer.no_padding()
    lengths = tokenizer.encode_batch([row[k] for split in splits.values() for row in split for k in ['sentence1', 'sentence2']])
    assert max(len(x.ids) for x in lengths) <= 256, 'No silently truncated training text is permitted'
    assert not texts(splits['train']) & heldout
    assert not texts(splits['validation'] + splits['calibration']) & texts(splits['test'])
    profiles = {}
    for name, values in splits.items():
        path = DATA / f'{name}.jsonl'
        path.write_text(''.join(json.dumps(row, ensure_ascii=False) + '\n' for row in values), encoding='utf-8')
        profiles[name] = {'rows': len(values), 'positive': sum(row['label'] == 1 for row in values), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}
    license_path = ROOT / 'data/research/PAWS-LICENSE.txt'
    assert license_path.exists()
    (DATA / 'PAWS-LICENSE.txt').write_bytes(license_path.read_bytes())
    model_license = DATA / 'MODEL-APACHE2-LICENSE.txt'
    if not model_license.exists():
        with urllib.request.urlopen('https://www.apache.org/licenses/LICENSE-2.0.txt', timeout=60) as response:
            license_bytes = response.read(50000)
        assert b'Apache License' in license_bytes
        model_license.write_bytes(license_bytes)
    report = {'purpose': 'Public paraphrase candidate, not AICTE incident matching training', 'publisher': 'Google Research', 'source': 'https://github.com/google-research-datasets/paws', 'licence': 'Google PAWS licence: freely usable for any purpose, preserve attribution and disclaimer', 'sources': sources, 'splits': profiles, 'removed': rejected, 'max_wordpieces': max(len(x.ids) for x in lengths), 'partition_policy': 'Official test untouched; official dev partitioned by connected normalized-sentence components into validation and calibration. All dev/test texts excluded from training. No extra artificial pairs, automatic complaint labels or test-driven checkpoint selection.', 'privacy': 'Wikipedia source entities; no complaint identities. Public complaint text is collected and audited separately.'}
    report['base_model_license'] = {'name': 'Apache-2.0', 'source': 'https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2', 'text_url': 'https://www.apache.org/licenses/LICENSE-2.0.txt', 'sha256': hashlib.sha256(model_license.read_bytes()).hexdigest()}
    RESULTS.mkdir(parents=True, exist_ok=True)
    (RESULTS / 'public-pairs-audit.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(report, indent=2), flush=True)


if __name__ == '__main__':
    main()
