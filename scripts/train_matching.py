"""Bounded reproducible MiniLM experiments; never activates a model."""
import argparse
import csv
import gc
import hashlib
import json
import platform
import random
import sys
import time
from datetime import datetime,timezone
from pathlib import Path
import numpy as np
import torch
from sentence_transformers import SentenceTransformer
from sentence_transformers.sentence_transformer.losses import ContrastiveLoss
ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT/'backend'))
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE','config.settings')
import django
django.setup()
from cases.management.commands.evaluate_matching import metrics,calibrate

def save(path,value):path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(value,indent=2),encoding='utf-8')
def seed():random.seed(26264);np.random.seed(26264);torch.manual_seed(26264)
def vectors(model,rows):return model.encode([r['text'] for r in rows],batch_size=32,normalize_embeddings=True,show_progress_bar=False)
def evaluate(matrix,rows,pairs,split,cut=None):
 index={r['id']:i for i,r in enumerate(rows)};selected=[p for p in pairs if p['split']==split]
 scores=np.array([float(matrix[index[p['left']]]@matrix[index[p['right']]]) for p in selected])
 labels=np.array([p['label']!='unrelated' for p in selected])
 if cut is None:
  result=calibrate(scores,labels)
  if result is None:return {'calibration_passed':False,'f1':0,'precision':0,'recall':0}
  cut=result[0]
 result={'threshold':cut,**metrics(scores,labels,cut),'calibration_passed':True}
 queries=[r for r in rows if r['split']==split and r['id'].endswith('-b')];hits=[]
 for query in queries:
  available=[r for r in rows if r['institution']==query['institution'] and r['id']!=query['id'] and not r['id'].endswith('-b')]
  top=sorted(available,key=lambda r:float(matrix[index[query['id']]]@matrix[index[r['id']]]),reverse=True)[:5]
  hits.append(query['id'][:-1]+'a' in {r['id'] for r in top})
 result['recall_at_5']=sum(hits)/len(hits) if hits else 0;result['retrieval_queries']=len(hits)
 return result

def train_epoch(model,pairs,device,batch_size=8,accumulation=4,max_batches=None):
 model.train();loss_fn=ContrastiveLoss(model);optimizer=torch.optim.AdamW(model.parameters(),lr=2e-5,weight_decay=0.01)
 values=list(pairs);random.shuffle(values);optimizer.zero_grad();started=time.perf_counter();losses=[]
 batches=[values[i:i+batch_size] for i in range(0,len(values),batch_size)]
 if max_batches:batches=batches[:max_batches]
 for step,batch in enumerate(batches):
  features=[{k:v.to(device) if isinstance(v,torch.Tensor) else v for k,v in model.tokenize([p[i] for p in batch]).items()} for i in (0,1)]
  labels=torch.tensor([p[2] for p in batch],dtype=torch.float32,device=device)
  loss=loss_fn(features,labels);(loss/accumulation).backward();losses.append(float(loss.detach()))
  if (step+1)%accumulation==0 or step+1==len(batches):
   torch.nn.utils.clip_grad_norm_(model.parameters(),1.0);optimizer.step();optimizer.zero_grad()
 return {'seconds':time.perf_counter()-started,'batches':len(batches),'mean_loss':float(np.mean(losses))}

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--epochs',type=int,default=3);parser.add_argument('--paws-limit',type=int,default=1024);args=parser.parse_args()
 if not 1<=args.epochs<=3:raise ValueError('Use one to three epochs.')
 seed();torch.set_num_threads(2);torch.set_num_interop_threads(2)
 data_path=ROOT/'data/research/education_pairs.json';corpus=json.loads(data_path.read_text(encoding='utf-8'));rows,pairs=corpus['records'],corpus['pairs'];index={r['id']:r for r in rows}
 assert all(index[p['left']]['split']==index[p['right']]['split']==p['split'] for p in pairs)
 families={s:{r['family'] for r in rows if r['split']==s} for s in ['train','validation','calibration','test']}
 assert all(not families[a]&families[b] for a in families for b in families if a!=b)
 train=[(index[p['left']]['text'],index[p['right']]['text'],float(p['label']!='unrelated')) for p in pairs if p['split']=='train']
 run=ROOT/'models/experiments'/datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ');run.mkdir(parents=True)
 device='cuda' if torch.cuda.is_available() else 'cpu';base_path=ROOT/'models/minilm';started=time.perf_counter()
 output={'run':str(run),'dataset_sha256':hashlib.sha256(data_path.read_bytes()).hexdigest(),'provenance':corpus['provenance'],'device':device,'hardware':{'platform':platform.platform(),'torch':torch.__version__,'gpu':torch.cuda.get_device_name(0) if device=='cuda' else 'CUDA unavailable in installed PyTorch; CPU fallback'},'batch_size':8,'gradient_accumulation':4,'epochs_limit':args.epochs,'learning_rate':2e-5,'splits':{s:len(f) for s,f in families.items()},'pair_counts':{s:sum(p['split']==s for p in pairs) for s in families},'variants':{}}
 model=SentenceTransformer(str(base_path),device=device,local_files_only=True);output['cold_load_seconds']=time.perf_counter()-started
 # Pilot is discarded so candidate initialization remains identical.
 batch_size=8
 while True:
  try:output['pilot']=train_epoch(model,train,device,batch_size,max_batches=4);break
  except torch.cuda.OutOfMemoryError:
   if batch_size==1:raise
   batch_size//=2;torch.cuda.empty_cache()
 output['batch_size']=batch_size;output['estimated_domain_epoch_seconds']=output['pilot']['seconds']/4*np.ceil(len(train)/batch_size)
 del model;gc.collect()
 for name in ['baseline','domain','paws_domain']:
  seed();model=SentenceTransformer(str(base_path),device=device,local_files_only=True);variant={'epochs':[]};dest=run/name
  if name=='paws_domain':
   path=ROOT/'data/research/paws_train.tsv'
   if not path.exists():output['variants'][name]={'skipped':'PAWS download unavailable; no substituted or fabricated training data'};continue
   with path.open(encoding='utf-8',newline='') as f:paws=list(csv.DictReader(f,delimiter='\t'))
   random.shuffle(paws);paws=paws[:args.paws_limit]
   variant['auxiliary']=train_epoch(model,[(p['sentence1'],p['sentence2'],float(p['label'])) for p in paws],device,batch_size)
   variant['auxiliary']['pairs']=len(paws)
  best=-1
  for epoch in range(0 if name=='baseline' else args.epochs):
   timing=train_epoch(model,train,device,batch_size);model.eval();matrix=vectors(model,rows)
   val=evaluate(matrix,rows,pairs,'validation');variant['epochs'].append({'epoch':epoch+1,**timing,'validation':val})
   if val['f1']>best:best=val['f1'];model.save(str(dest))
   save(ROOT/'reports/training-progress.json',{'current_variant':name,'results':output,'current':variant})
   print(name,'epoch',epoch+1,'validation_f1',round(val['f1'],4),flush=True)
  if name=='baseline':dest=base_path
  del model;gc.collect();model=SentenceTransformer(str(dest),device=device,local_files_only=True);matrix=vectors(model,rows)
  variant.update(path=str(dest),relative_path=dest.relative_to(ROOT/'models').as_posix(),validation=evaluate(matrix,rows,pairs,'validation'))
  output['variants'][name]=variant;del model;gc.collect()
 candidates=[n for n in ['domain','paws_domain'] if 'validation' in output['variants'][n]]
 candidate=max(candidates,key=lambda n:output['variants'][n]['validation']['f1']);output['candidate_selected_on_validation']=candidate
 # Test only after the candidate and checkpoints have been frozen.
 for name in ['baseline',candidate]:
  variant=output['variants'][name];model=SentenceTransformer(variant['path'],device=device,local_files_only=True);matrix=vectors(model,rows)
  calibration=evaluate(matrix,rows,pairs,'calibration');variant['calibration']=calibration
  if calibration['calibration_passed']:variant['test']=evaluate(matrix,rows,pairs,'test',calibration['threshold'])
  variant['checkpoint_sha256']=hashlib.sha256((Path(variant['path'])/'model.safetensors').read_bytes()).hexdigest() if (Path(variant['path'])/'model.safetensors').exists() else None
  del model;gc.collect()
 base=output['variants']['baseline'].get('test',{});test=output['variants'][candidate].get('test',{})
 passes=bool(test and test['precision']>=.85 and test['recall_at_5']>=.90 and test['f1']>base.get('f1',1))
 output.update(candidate_passes_synthetic_gate=passes,active_model='baseline',promotion='No automatic promotion: independent human review remains pending even when synthetic gates pass.',total_seconds=time.perf_counter()-started,peak_cuda_bytes=torch.cuda.max_memory_allocated() if device=='cuda' else 0)
 save(run/'experiment.json',output);save(ROOT/'reports/training.json',output)
 print(json.dumps({'candidate':candidate,'passes_synthetic_gate':passes,'active_model':'baseline','seconds':output['total_seconds']}),flush=True)
if __name__=='__main__':main()
