"""Non-executing public XLSX intake; records metadata, never invents incident labels."""
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import unicodedata
import urllib.request
import zipfile
from openpyxl import load_workbook

METADATA='https://dataverse.harvard.edu/api/datasets/:persistentId/?persistentId=doi:10.7910/DVN/EITGBB'


def inspect_workbook(source):
    book=load_workbook(source,read_only=True,data_only=False,keep_links=False)
    text_headers={'text','message','description','complaint','feedback','query','remarks','subject'}
    label_headers={'category','module','nature','label','sentiment','type'}
    sheets=[]
    try:
        for sheet in book:
            rows=sheet.iter_rows();first=next(rows,());headers=[str(c.value or '').strip().casefold() for c in first]
            text_cols=[i for i,h in enumerate(headers) if h in text_headers];label_cols=[i for i,h in enumerate(headers) if h in label_headers]
            count=blank=formulas=formula_rows=pii_rows=literal_rows=0
            missing=[0]*len(headers);hashes=Counter();formula_columns=Counter();functions=Counter();labels={str(i):set() for i in label_cols};known_types=Counter()
            for row in rows:
                count+=1
                if not any(c.value is not None and c.value!='' for c in row):blank+=1
                has_formula=has_identifier=text_incomplete=False;texts=[]
                for i,cell in enumerate(row[:len(headers)]):
                    missing[i]+=cell.value is None or cell.value==''
                    if cell.data_type=='f':
                        formulas+=1;formula_columns[str(i)]+=1;has_formula=True
                        function=re.match(r'^[+=\s]*([A-Za-z_][A-Za-z0-9_.]*)\s*\(',str(cell.value))
                        if function:functions[function[1]]+=1
                        if i in text_cols:text_incomplete=True
                        continue
                    if i in text_cols and isinstance(cell.value,str):
                        texts.append(' '.join(unicodedata.normalize('NFKC',cell.value).casefold().split()))
                        has_identifier|=bool(re.search(r'[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}|(?<!\d)\d[\d -]{8,}\d(?!\d)',cell.value))
                    if i in label_cols and cell.value is not None:labels[str(i)].add(str(cell.value))
                    if i in label_cols and headers[i]=='type' and str(cell.value).casefold().strip() in {'complaint','support','suggestion','appreciation','request','feedback','other','others'}:
                        known_types[str(cell.value).casefold().strip()]+=1
                formula_rows+=has_formula;pii_rows+=has_identifier
                if texts and not text_incomplete:
                    literal_rows+=1;hashes[hashlib.sha256(json.dumps(texts,ensure_ascii=False).encode()).hexdigest()]+=1
            assert count==blank+(count-blank) and formulas==sum(formula_columns.values())
            sheets.append({'sheet':sheet.title,'physical_data_rows':count,'nonempty_rows':count-blank,'blank_rows':blank,'columns':len(headers),
                'recognized_headers':{str(i):h for i,h in enumerate(headers) if h in text_headers|label_headers},'missing_by_column':missing,
                'formula_cells_not_executed':formulas,'formula_rows':formula_rows,'formula_cells_by_column':dict(formula_columns),'formula_function_names_only':dict(functions),
                'text_columns_recognized':text_cols,'complete_literal_text_rows':literal_rows,'duplicate_complete_literal_text_rows':sum(n-1 for n in hashes.values()),
                'rows_with_potential_identifier_patterns':pii_rows,'label_cardinality_by_column':{k:len(v) for k,v in labels.items()},'recognized_type_counts':dict(known_types)})
    finally:book.close()
    return sheets


def collect(workspace, report):
    root=Path(workspace).resolve()
    if not root.is_relative_to(Path('data/research').resolve()) or not root.is_dir():raise ValueError('Existing private research workspace required.')
    def get(url,limit):
        with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'SIH26264-public-source-audit/1.0'}),timeout=40) as response:
            raw=response.read(limit+1)
        if len(raw)>limit:raise ValueError('Source exceeds the declared intake limit.')
        return raw
    metadata_raw=get(METADATA,2_000_000);metadata=json.loads(metadata_raw);version=metadata['data']['latestVersion']
    licence=version.get('license',{})
    if version['versionState']!='RELEASED' or licence.get('name')!='CC BY-NC 4.0':raise ValueError('Recheck the released source and current use conditions.')
    file=next(row for row in version['files'] if row['dataFile']['filename']=='ACSSv1.xlsx')
    if file.get('restricted'):raise ValueError('Restricted source requires separate permission.')
    info=file['dataFile'];content=get(f'https://dataverse.harvard.edu/api/access/datafile/{int(info["id"])}',20_000_000)
    assert len(content)==info['filesize']
    assert info['checksum']['type']=='MD5' and hashlib.md5(content).hexdigest()==info['checksum']['value']
    source=root/'acss.xlsx'
    with source.open('xb') as stream:stream.write(content)
    with (root/'publisher-metadata.json').open('xb') as stream:stream.write(metadata_raw)
    with zipfile.ZipFile(source) as archive:
        if sum(item.file_size for item in archive.infolist())>100_000_000:raise ValueError('Excessive expanded workbook size.')
        if any('vbaproject' in item.filename.lower() for item in archive.infolist()):raise ValueError('Macro workbook not accepted.')
    sheets=inspect_workbook(source)
    result={'source':'ACSS (AICTE Centralized Support System) Data Set','doi':'10.7910/DVN/EITGBB','metadata_url':METADATA,
        'collected_at_utc':datetime.now(timezone.utc).isoformat(),'version':str(version['versionNumber'])+'.'+str(version['versionMinorNumber']),
        'publisher_license':licence,'article_license_discrepancy':'Article describes CC BY 4.0; current Dataverse metadata specifies CC BY-NC 4.0. Raw data is retained privately and not redistributed.',
        'file_id':info['id'],'filename':info['filename'],'bytes':len(content),'sha256':hashlib.sha256(content).hexdigest(),'publisher_checksum':info['checksum'],
        'sheets':sheets,'identity_and_incident_labels':'Sentiment/support classification is documented; no independent same-incident ground truth established.',
        'deidentification':'Unverified; pattern counts are screening signals, not proof of anonymity. No raw cells included in this report.',
        'application_imported':False,'model_scored':False,'trained':False,'real_world_matching_accuracy':None,
        'next_gate':'Verify fields/identity and complete independent incident annotation before any incident accuracy or training claim.'}
    with Path(report).open('x',encoding='utf-8') as stream:json.dump(result,stream,indent=2)
    return result
