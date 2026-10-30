"""Collect reproducible public auxiliary data; never execute downloaded SQL."""
import csv
import hashlib
import io
import json
import sys
import tarfile
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT/'backend'))
from cases.demo_data import TOPICS

def download(url):
 req=urllib.request.Request(url,headers={'User-Agent':'AICTE-SIH-research-prototype/1.0'})
 with urllib.request.urlopen(req,timeout=90) as response:
  data=response.read(40*1024*1024+1)
 if len(data)>40*1024*1024: raise ValueError('Download exceeds 40 MB.')
 return data

def synthetic():
 topics=[(cat,*pair) for cat,items in TOPICS.items() for pair in items]
 # Hold whole allegation templates together, not just substituted family IDs.
 group_splits=['train']*11+['validation']*3+['calibration']*2+['test']*2
 records=[];pairs=[]
 for family in range(360):
  topic=family%18; split=group_splits[topic]; category,a,b=topics[topic]
  year=2022+(family//18)%4; cohort=family+1
  a=a.format(year=year);b=b.format(year=year)
  allowed=[i for i in range(18) if group_splits[i]==split and i!=topic]
  neg=topics[allowed[family%len(allowed)]][1].format(year=year)
  suffix=f' Programme cohort {cohort}; fictional complaint only.'
  texts={'a':a+suffix,'b':b+f' The affected programme intake is {cohort}. Synthetic report.',
   'r':topics[topic][1].format(year=year-1)+f' A separate incident in the previous year; cohort {cohort}.',
   's':a+f' This is a separate student request in cohort {cohort}; review for a shared institutional issue.',
   'n':neg+suffix}
  for key,text in texts.items():records.append({'id':f'{family}-{key}','family':family,'template_group':topic,'split':split,'institution':f'DEMO-{family%30+1:04d}','category':category,'text':text,'provenance':'synthetic_authored_unreviewed'})
  for key,label in [('b','same_incident'),('r','related_issue'),('s','related_issue'),('n','unrelated')]:pairs.append({'left':f'{family}-a','right':f'{family}-{key}','label':label,'split':split,'family':family})
 groups={s:{r['template_group'] for r in records if r['split']==s} for s in set(group_splits)}
 assert all(not groups[a]&groups[b] for a in groups for b in groups if a!=b)
 assert len(pairs)>=1000 and len({r['family'] for r in records})>=300
 return {'provenance':'Authored synthetic education allegations; no independent human review or real-world accuracy claim. Entire allegation templates and incident families held within one partition. Different-institution controls belong to retrieval filtering, not text-only negative training.', 'records':records,'pairs':pairs}

def main():
 dest=ROOT/'data'/'research';dest.mkdir(parents=True,exist_ok=True)
 source=[{'name':'Synthetic education pairs','status':'generated','license':'Project-authored synthetic data','personal_identifiers':'none; fictional cohorts','label_meaning':['same_incident','related_issue','unrelated'],'human_review':'pending'}]
 domain=synthetic();(dest/'education_pairs.json').write_text(json.dumps(domain,indent=2),encoding='utf-8')
 with (dest/'education_pair_review.csv').open('w',encoding='utf-8',newline='') as f:
  writer=csv.writer(f);writer.writerow(['left_id','right_id','left_text','right_text','authored_label','human_label','reviewer','reason','split'])
  lookup={r['id']:r['text'] for r in domain['records']}
  for pair in domain['pairs']:writer.writerow([pair['left'],pair['right'],lookup[pair['left']],lookup[pair['right']],pair['label'],'','','',pair['split']])
 source[0].update(records=len(domain['records']),pairs=len(domain['pairs']),incident_families=360,missing_text=0,language='English',duplicate_text=len(domain['records'])-len({r['text'] for r in domain['records']}))
 try:
  url='https://storage.googleapis.com/paws/english/paws_wiki_labeled_final.tar.gz';raw=download(url)
  (dest/'paws_wiki_labeled_final.tar.gz').write_bytes(raw)
  counts={}; profiles={}
  with tarfile.open(fileobj=io.BytesIO(raw),mode='r:gz') as tar:
   if sum(m.size for m in tar.getmembers())>100*1024*1024:raise ValueError('Expanded archive too large.')
   for split in ['train','dev','test']:
    members=[m for m in tar.getmembers() if m.name.endswith('/'+split+'.tsv')]
    if len(members)!=1:raise ValueError('Unexpected PAWS archive layout.')
    content=tar.extractfile(members[0]).read().decode('utf-8')
    rows=list(csv.DictReader(io.StringIO(content),delimiter='\t'))
    assert all(r['label'] in ('0','1') and r['sentence1'] and r['sentence2'] for r in rows)
    (dest/f'paws_{split}.tsv').write_text(content,encoding='utf-8')
    counts[split]=len(rows);profiles[split]={'missing_text':0,'duplicate_pairs':len(rows)-len({(r['sentence1'],r['sentence2']) for r in rows})}
  license_text=download('https://raw.githubusercontent.com/google-research-datasets/paws/master/LICENSE').decode()
  (dest/'PAWS-LICENSE.txt').write_text(license_text,encoding='utf-8')
  source.append({'name':'PAWS-Wiki Labeled Final','status':'downloaded','url':url,'source':'https://github.com/google-research-datasets/paws','sha256':hashlib.sha256(raw).hexdigest(),'license':'See PAWS-LICENSE.txt; preserve acknowledgement','language':'English','fields':['id','sentence1','sentence2','label'],'labels':'1 paraphrase, 0 different meaning; not complaint incident labels','counts':counts,'profile':profiles,'personal_identifiers':'Wikipedia entities; no claim of anonymization','access':'public archive; published splits retained'})
 except Exception as exc:
  archive_error=str(exc)
  try:
   import pyarrow.parquet as pq
   listing=json.loads(download('https://huggingface.co/api/datasets/google-research-datasets/paws/tree/main/labeled_final'))
   counts={};profiles={};hashes={}
   for item in listing:
    path=item['path'];split=Path(path).name.split('-')[0];outsplit='dev' if split=='validation' else split
    raw=download('https://huggingface.co/datasets/google-research-datasets/paws/resolve/main/'+path)
    assert hashlib.sha256(raw).hexdigest()==item['lfs']['oid']
    (dest/Path(path).name).write_bytes(raw)
    rows=pq.read_table(io.BytesIO(raw)).to_pylist()
    assert all(r['label'] in (0,1) and r['sentence1'] and r['sentence2'] for r in rows)
    with (dest/f'paws_{outsplit}.tsv').open('w',encoding='utf-8',newline='') as f:
     writer=csv.DictWriter(f,fieldnames=['id','sentence1','sentence2','label'],delimiter='\t');writer.writeheader();writer.writerows(rows)
    counts[outsplit]=len(rows);hashes[split]=hashlib.sha256(raw).hexdigest();profiles[outsplit]={'missing_text':0,'duplicate_pairs':len(rows)-len({(r['sentence1'],r['sentence2']) for r in rows})}
   (dest/'PAWS-LICENSE.txt').write_text(download('https://raw.githubusercontent.com/google-research-datasets/paws/master/LICENSE').decode(),encoding='utf-8')
   source.append({'name':'PAWS-Wiki Labeled Final','status':'downloaded','source':'https://huggingface.co/datasets/google-research-datasets/paws','original_archive_error':archive_error,'sha256':hashes,'counts':counts,'profile':profiles,'license':'See PAWS-LICENSE.txt; preserve acknowledgement','fields':['id','sentence1','sentence2','label'],'language':'English','labels':'1 paraphrase, 0 different meaning; not complaint incident labels','access':'Public publisher dataset mirror; original train/validation/test partitions retained','personal_identifiers':'Wikipedia entities; not an anonymized grievance corpus'})
  except Exception as fallback:source.append({'name':'PAWS-Wiki','status':'download_failed','error':archive_error,'fallback_error':str(fallback)})
 try:
  url='https://data.mendeley.com/datasets/w2cp7h53s5/1'
  endpoint='https://data.mendeley.com/public-api/datasets/w2cp7h53s5/files?folder_id=root&version=1&$start=0&$limit=1000'
  req=urllib.request.Request(endpoint,headers={'Accept':'application/vnd.mendeley-public-dataset.1+json','User-Agent':'AICTE-SIH-research-prototype/1.0'})
  with urllib.request.urlopen(req,timeout=90) as response:listing=json.loads(response.read())
  entry=next(x for x in listing if x['filename']=='Complaints_Reports_Data.sql')
  raw=download(entry['content_details']['download_url'])
  assert hashlib.sha256(raw).hexdigest()==entry['content_details']['sha256_hash']
  (dest/'Complaints_Reports_Data.sql').write_bytes(raw)
  status='downloaded_pending_audit';error='SQL parsed as data only; never executed.'
 except Exception as exc:status='access_failed';error=str(exc)
 source.append({'name':'IIIT Delhi Indian complaint tweets','url':url,'status':status,'error':error,'license':'CC BY 4.0 stated by publisher','fields':['tweet text','timestamp','organization','complaint_or_unknown'],'labels':'complaint vs unknown; no overlap labels','language':'must inspect after access','record_count':None,'personal_identifiers':'Publisher lists user names, locations and user IDs; remove before use','training_use':'excluded until payload and privacy review verified'})
 source.append({'name':'DARPG 2024','url':'https://innovateindia.mygov.in/darpg-challenge-2024/','status':'restricted_access_not_collected','access':'Challenge registrants; 2024 registration closed','record_count':None,'license':'No public training license verified','training_use':'excluded; obtain authorized sample separately'})
 (dest/'source_register.json').write_text(json.dumps({'collected_at':datetime.now(timezone.utc).isoformat(),'sources':source},indent=2),encoding='utf-8')
 if status=='downloaded_pending_audit':
  from audit_indian_complaints import main as audit
  audit()
 print(json.dumps({'education_pairs':len(domain['pairs']),'sources':[{'name':s['name'],'status':s['status']} for s in source]},indent=2))
if __name__=='__main__':main()
