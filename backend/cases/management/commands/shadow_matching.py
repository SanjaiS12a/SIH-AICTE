"""Synthetic-only shadow experiment with PostgreSQL fixture rollback."""
import json
import time
import uuid
from collections import Counter
from pathlib import Path
from django.conf import settings
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError
from django.db import connection, transaction
from django.test import override_settings
from django.utils import timezone
from cases.models import Bureau, Institution, Membership, Complaint
from cases.matching import encoder, runtime
from cases.shadow import discover
from cases.management.commands.evaluate_matching import eligible_corpus


class Command(BaseCommand):
    help = 'Explicit synthetic shadow experiment; production suggestions and data remain unchanged.'

    def add_arguments(self, parser):
        parser.add_argument('--enable-shadow', action='store_true')
        parser.add_argument('--data', required=True)
        parser.add_argument('--output', required=True)
        parser.add_argument('--budget', type=int, default=20)

    def handle(self, *args, **options):
        if not options['enable_shadow'] or not connection.settings_dict['NAME'].startswith(('coordination_audit', 'coordination_scale_')):
            raise CommandError('Explicit shadow opt-in and an isolated audit/scale database are required.')
        target = Path(options['output']).resolve(); allowed = (settings.RESULTS_DIR/'runs').resolve()
        if not target.is_relative_to(allowed) or target.exists(): raise CommandError('Use a new ignored run output.')
        corpus = json.loads(Path(options['data']).read_text(encoding='utf-8'))
        if 'synthetic' not in corpus.get('label_provenance','').lower():
            raise CommandError('This database-backed fixture runner accepts synthetic data only. Authentic corpora stay outside application databases.')
        rows, _, labels, eligibility = eligible_corpus(corpus)
        _, revision, cutoff = runtime(); model = encoder()
        ids = sorted(rows); vectors = model.encode([rows[key]['text'] for key in ids],normalize_embeddings=True,batch_size=32)
        results = []; token = uuid.uuid4().hex[:12]
        before = Complaint.objects.count()
        with transaction.atomic(), override_settings(SHADOW_RETRIEVAL_ENABLED=True):
            user = User.objects.create(username='shadow-'+token)
            Membership.objects.create(user=user,role='coordinator')
            bureau = Bureau.objects.create(code='SH-'+token,name='Synthetic shadow fixtures')
            institutions = {value: Institution.objects.create(name='Synthetic '+value,permanent_id='SH-'+token+'-'+value)
                            for value in {r['institution'] for r in rows.values()}}
            cases = {}
            for key, vector in zip(ids,vectors):
                row = rows[key]
                cases[key] = Complaint.objects.create(reference='SH-'+token+'-'+key,submission_id=uuid.uuid4(),
                    institution=institutions[row['institution']],bureau=bureau,created_by=user,source_system='shadow-'+token,
                    source_reference=key,category='administration',summary=row['text'],description='Synthetic evaluation fixture.',
                    received_at=timezone.now(),due_at=timezone.now(),embedding=vector.tolist(),model_revision=revision,matching_state='complete')
            query_ids = {q['query'] for q in corpus['retrieval']}
            # Discovery must exclude other query complaints, matching B1's reference-corpus protocol.
            Complaint.objects.filter(pk__in=[case.pk for key,case in cases.items() if key in query_ids]).update(embedding=None)
            for query in corpus['retrieval']:
                key = query['query']
                if key not in rows or query['split'] not in ['calibration','test']: continue
                case = cases[key]
                # Lexical/reference candidates also exclude query records and the other partition.
                base = Complaint.objects.filter(pk__in=[c.pk for ident,c in cases.items() if ident not in query_ids and rows[ident]['split']==query['split']])
                started = time.perf_counter()
                result = discover(user,case,options['budget'], list(base.values_list('pk',flat=True)))
                elapsed = (time.perf_counter()-started)*1000
                reverse = {str(c.pk):ident for ident,c in cases.items()}
                result = {**result,'query':key,'split':query['split'],'milliseconds':elapsed}
                for method in ['baseline','lexical','reference','union']:
                    result[method] = [reverse[value] for value in result[method]]
                result['bounded_union'] = [reverse[value] for value in result['bounded_union']]
                result['candidate_ids_by_channel'] = {method:[reverse[value] for value in values] for method,values in result['candidate_ids_by_channel'].items()}
                result['relevant'] = query['relevant']
                results.append(result)
            transaction.set_rollback(True)
        if Complaint.objects.filter(source_system='shadow-'+token).exists() or User.objects.filter(username='shadow-'+token).exists():
            raise CommandError('Shadow fixture rollback verification failed.')
        counts_unchanged = Complaint.objects.count() == before
        metrics = {}
        for split in ['calibration','test']:
            selected = [r for r in results if r['split']==split]
            metrics[split] = {}
            for method in ['baseline','lexical','reference','union']:
                returned = [(r['query'],key) for r in selected for key in r[method]]
                judged = [labels.get(tuple(sorted(pair))) for pair in returned]
                usable = [label for label in judged if label]
                hits = sum(bool(set(r[method]) & set(r['relevant'])) for r in selected)
                metrics[split][method] = {'queries':len(selected),'suggestions':len(returned),'judged':len(usable),
                    'precision':sum(v!='unrelated' for v in usable)/len(returned) if returned and len(usable)==len(returned) else None,
                    'label_coverage':len(usable)/len(returned) if returned else None,
                    'query_coverage':sum(bool(r[method]) for r in selected)/len(selected) if selected else None,
                    'mean_reciprocal_rank':sum(next((1/(i+1) for i,key in enumerate(r[method]) if key in r['relevant']),0) for r in selected)/len(selected) if selected else None,
                    'same_incident_query_hit_rate_at5':hits/len(selected) if selected else None}
            positives=sum(len(r['relevant']) for r in selected)
            metrics[split]['bounded_candidate_recall']=sum(len(set(r['bounded_union']) & set(r['relevant'])) for r in selected)/positives if positives else None
        output = {'mode':'disabled-by-default synthetic shadow only','model_revision':revision,'threshold':cutoff,
            'fixture_rollback_verified':True,'complaint_count_unchanged':counts_unchanged,'eligibility':eligibility,'metrics':metrics,'results':results,
            'activation':'Not approved: no independent real-domain judgments; no policy selection from held-out test.',
            'limits':'Synthetic metadata; unique record IDs provide no shared-reference ground truth. RRF is fixed for this diagnostic, not calibrated or activated.'}
        target.parent.mkdir(parents=True,exist_ok=True)
        with target.open('x',encoding='utf-8') as stream: json.dump(output,stream,indent=2)
        self.stdout.write(json.dumps({'output':str(target),'queries':len(results),'fixture_rollback_verified':True,'complaint_count_unchanged':counts_unchanged,'metrics':metrics}))
