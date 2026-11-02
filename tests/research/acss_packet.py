"""Prepare private, unscored candidates; privacy clearance and incident labels stay pending."""
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path
from openpyxl import load_workbook
from .public_corpus import redact, write_new
from .public_evaluation import blind_files

SOURCE_SHA256='afd843068ddd36d65905f3e6b99ff201ddcc6405a297abf2ef3eeafdd351c55a'


def candidate_rows(source, limit=20):
    book=load_workbook(source,read_only=True,data_only=False,keep_links=False)
    seen=set();selected=[];excluded=Counter()
    try:
        rows=book.worksheets[0].iter_rows();headers=[str(c.value or '').casefold().strip() for c in next(rows)]
        columns={name:headers.index(name) for name in ('subject','description','type')}
        for number,row in enumerate(rows,2):
            if str(row[columns['type']].value).casefold().strip()!='complaint':continue
            cells=[row[columns[key]] for key in ('subject','description')]
            if any(cell.data_type=='f' or not isinstance(cell.value,str) or not cell.value.strip() for cell in cells):
                excluded['formula_or_missing_literal_text']+=1;continue
            original='\n'.join(f'{key}: {cell.value.strip()}' for key,cell in zip(('Subject','Description'),cells))
            digest=hashlib.sha256(' '.join(original.casefold().split()).encode()).hexdigest()
            if digest in seen:excluded['repeated_text']+=1;continue
            seen.add(digest)
            if not 80<=len(original)<=4000:excluded['length_outside_candidate_bounds']+=1;continue
            masked,changes=redact(original)
            if len(selected)<limit:
                selected.append({'id':f'ACSS-ROW-{number}','source_id':str(number),'source_url':'https://doi.org/10.7910/DVN/EITGBB',
                    'text_type':'Original published support subject/description; automated masking, not privacy-certified',
                    'category':'Literal Complaint type; incident identity unknown','model_text':masked,'source_text_sha256':digest,
                    'redaction_counts':changes,'entity':None,'institution_id':None,'incident_group':None})
    finally:book.close()
    return selected,dict(excluded)


def prepare(workspace):
    workspace=Path(workspace).resolve()
    if not workspace.is_relative_to(Path('data/research').resolve()):raise ValueError('Private research workspace required.')
    source=workspace/'acss.xlsx'
    if hashlib.sha256(source.read_bytes()).hexdigest()!=SOURCE_SHA256:raise ValueError('Re-audit changed source before preparing a packet.')
    destination=workspace/'annotation-candidates';destination.mkdir(mode=0o700,exist_ok=False)
    records,excluded=candidate_rows(source)
    if len(records)!=20:raise ValueError('Inspect source quality before changing candidate selection.')
    write_new(destination/'records-private.json',records)
    pairs=[{'pair_id':f'acss-unscored-{n//2+1}','query_id':records[n]['id'],'reference_id':records[n+1]['id']} for n in range(0,len(records),2)]
    blind_files(destination,'acss',pairs,{row['id']:row for row in records})
    with (destination/'privacy-and-identity-review.csv').open('x',encoding='utf-8',newline='') as target:
        fields=['record_id','privacy_reviewer','privacy_decision','genuine_institution_evidence','incident_family_evidence','permission_reference','reason','status']
        writer=csv.DictWriter(target,fieldnames=fields);writer.writeheader()
        writer.writerows({'record_id':row['id'],'status':'pending'} for row in records)
    result={'source_sha256':SOURCE_SHA256,'candidate_records':len(records),'unscored_pairs':len(pairs),'excluded':excluded,
        'selection':'First 20 bounded unique literal Complaint-labelled narratives in source order; not a representative sample.',
        'redaction_counts':dict(Counter({kind:sum(change['count'] for row in records for change in row['redaction_counts'] if change['kind']==kind) for kind in {c['kind'] for row in records for c in row['redaction_counts']}})),
        'privacy_review_completed':False,'institution_identity_verified':False,'independent_labels':0,
        'evaluation_permitted':False,'training_permitted':False,'redistribution_permitted':False,'model_scored':False,
        'limits':'Automated masking misses names/contextual identifiers. Review files remain restricted; permission, privacy and genuine entity gates precede annotation use. Unscored adjacent pairs are not same-incident or eligible retrieval labels.'}
    write_new(destination/'manifest.json',result)
    (destination/'READ-ME-FIRST.txt').write_text('Do not distribute or score this packet. Read docs/acss-annotation-handoff.md and clear privacy, identity and permission gates first. All judgments are blank.\n',encoding='utf-8')
    return result
