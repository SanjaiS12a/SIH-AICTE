"""Versioned staging and transactional activation/rollback of local encoders."""
import json
import math
from pathlib import Path
from django.conf import settings
from django.core.management.base import BaseCommand,CommandError
from django.db import transaction,connection
from django_q.tasks import async_task
from cases.models import Complaint,Institution,ModelRelease,StagedEmbedding
from cases.matching import runtime

def swap_release(release):
 if not release.approved:raise CommandError('Release is not approved; independent human review and evaluation gates are required.')
 with transaction.atomic():
  list(Institution.objects.select_for_update().order_by('id').values_list('id',flat=True))
  # Readers see the embedding replacement and active revision in one commit.
  populated=Complaint.objects.filter(embedding__isnull=False)
  if populated.exclude(pk__in=StagedEmbedding.objects.filter(revision=release.revision).values('case_id')).exists():raise CommandError('Backfill incomplete; stage again before activation.')
  with connection.cursor() as cursor:
   cursor.execute("UPDATE cases_complaint c SET embedding=s.embedding, model_revision=%s, matching_state='pending' FROM cases_stagedembedding s WHERE s.case_id=c.id AND s.revision=%s",[release.revision,release.revision])
  ModelRelease.objects.filter(active=True).update(active=False)
  release.active=True;release.save(update_fields=['active'])
  async_task('cases.management.commands.model_release.refresh_active_matches')

def refresh_active_matches():
 from cases.matching import match_batch
 ids=list(Complaint.objects.filter(matching_state='pending').values_list('pk',flat=True)[:64])
 if not ids:return
 try:match_batch([str(pk) for pk in ids])
 finally:
  if Complaint.objects.filter(matching_state='pending').exists():async_task('cases.management.commands.model_release.refresh_active_matches')

class Command(BaseCommand):
 help='Stage a model without activating it; activate/rollback only an approved, fully backfilled revision.'
 def add_arguments(self,parser):
  parser.add_argument('action',choices=['stage','activate','rollback'])
  parser.add_argument('--revision',required=True);parser.add_argument('--path');parser.add_argument('--threshold',type=float);parser.add_argument('--report')
 def handle(self,*args,**opts):
  name=opts['revision']
  if opts['action']!='stage':
   try:release=ModelRelease.objects.get(revision=name)
   except ModelRelease.DoesNotExist:raise CommandError('Stage this revision first.')
   swap_release(release);self.stdout.write(f'Activated {name}; pending suggestions will refresh.');return
  if not opts['path'] or opts['threshold'] is None or not math.isfinite(opts['threshold']) or not 0<=opts['threshold']<=1:raise CommandError('Supply a local model --path and threshold between zero and one.')
  root=Path(settings.MODEL_PATH).resolve().parent;path=(root/opts['path']).resolve()
  if not path.is_relative_to(root) or not path.is_dir():raise CommandError('Model path must be inside the configured models directory.')
  if ModelRelease.objects.filter(revision=name,active=True).exists():raise CommandError('Do not restage the active revision.')
  existing=ModelRelease.objects.filter(revision=name).first()
  approved=bool(existing and existing.approved and existing.path==path.relative_to(root).as_posix() and existing.threshold==opts['threshold'])
  if opts['report']:
   report=json.loads(Path(opts['report']).read_text(encoding='utf-8'))
   candidate=report['variants'][report['candidate_selected_on_validation']]
   approved=bool(report.get('human_review_completed') and report.get('candidate_passes_synthetic_gate') and ((root/candidate['relative_path']).resolve() if candidate.get('relative_path') else Path(candidate['path']).resolve())==path and candidate['calibration']['threshold']==opts['threshold'])
  from sentence_transformers import SentenceTransformer
  model=SentenceTransformer(str(path),device='cpu',local_files_only=True)
  if model.get_sentence_embedding_dimension()!=384:raise CommandError('Expected 384-dimensional model.')
  baseline_path,baseline_revision,baseline_threshold=runtime()
  baseline,_=ModelRelease.objects.get_or_create(revision=baseline_revision,defaults={'path':Path(baseline_path).resolve().relative_to(root).as_posix(),'threshold':baseline_threshold,'active':True,'approved':True})
  for start in range(0,Complaint.objects.filter(embedding__isnull=False).count(),256):
   old=list(Complaint.objects.filter(embedding__isnull=False).order_by('pk')[start:start+256])
   StagedEmbedding.objects.bulk_create([StagedEmbedding(case=c,revision=baseline_revision,embedding=c.embedding) for c in old],ignore_conflicts=True,batch_size=256)
  release,_=ModelRelease.objects.update_or_create(revision=name,defaults={'path':path.relative_to(root).as_posix(),'threshold':opts['threshold'],'approved':approved})
  last=None;count=0
  while True:
   qs=Complaint.objects.order_by('pk')
   if last:qs=qs.filter(pk__gt=last)
   rows=list(qs[:128])
   if not rows:break
   embeddings=model.encode([c.summary for c in rows],batch_size=32,normalize_embeddings=True)
   StagedEmbedding.objects.bulk_create([StagedEmbedding(case=c,revision=name,embedding=v.tolist()) for c,v in zip(rows,embeddings)],update_conflicts=True,unique_fields=['case','revision'],update_fields=['embedding'],batch_size=128)
   last=rows[-1].pk;count+=len(rows)
  self.stdout.write(f'Staged {count} embeddings; approved={approved}. Active baseline retained.')
