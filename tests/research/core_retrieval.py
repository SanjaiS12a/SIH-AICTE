"""Frozen-model diagnostic in a new synthetic research database, never a demo DB."""
import hashlib
import json
from pathlib import Path
import resource
import time
import uuid
import numpy as np
from django.db import connection
from django.test import override_settings
from django.utils import timezone
from cases.models import Institution, Bureau, Membership, Complaint
from cases.matching import encoder, tokenizer, runtime
from cases.shadow import discover
from .representations import representations, POLICY


def run(input_path, output_path):
    if not connection.settings_dict['NAME'].startswith('coordination_core_research_'):
        raise ValueError('A fresh coordination_core_research_* database is required.')
    if Complaint.objects.exists(): raise ValueError('Refusing to modify an existing corpus.')
    out=Path(output_path);out.mkdir(parents=True,exist_ok=False)
    raw=Path(input_path).read_bytes();dataset=json.loads(raw)
    if not dataset.get('provenance','').startswith('Authored synthetic'):raise ValueError('This diagnostic accepts the declared synthetic fixture only.')
    records=dataset['records'];by_id={r['id']:r for r in records}
    if len(records)>2000 or len(by_id)!=len(records):raise ValueError('Bounded unique corpus required.')
    labels={(row['query'],row['reference']):row['label'] for row in dataset['labels']}
    from django.contrib.auth.models import User
    user=User.objects.create_user('core-research');Membership.objects.create(user=user,role='coordinator')
    bureau=Bureau.objects.create(code='CORE',name='Synthetic research scope')
    institutions={key:Institution.objects.create(permanent_id=key,name='Fictional research '+key,region='Synthetic',district='Synthetic') for key in {r['institution'] for r in records}}
    path,revision,cutoff=runtime();weights=Path(path)/'model.safetensors'
    before=hashlib.file_digest(weights.open('rb'),'sha256').hexdigest()
    started=time.perf_counter();model=encoder();load=time.perf_counter()-started
    token=tokenizer();versions={r['id']:representations(r,token) for r in records}
    for r in records:
        if not versions[r['id']]['representations']['summary']:raise ValueError('Baseline input must be eligible; no silent truncation.')
    texts=list(dict.fromkeys(item['text'] for result in versions.values() for items in result['representations'].values() for item in items))
    started=time.perf_counter();vectors=model.encode(texts,normalize_embeddings=True,batch_size=32);embedding_seconds=time.perf_counter()-started
    indexes={text:i for i,text in enumerate(texts)}
    cases={}
    for n,r in enumerate(records):
        cases[r['id']]=Complaint.objects.create(reference=f'CORE-{n}',submission_id=uuid.uuid4(),institution=institutions[r['institution']],bureau=bureau,created_by=user,
            source_system='core-'+r['id'][:30],source_reference=r['source_reference'],category=r['category'],summary=r['summary'],description=r['description'],
            received_at=timezone.now(),due_at=timezone.now(),embedding=vectors[indexes[r['summary']]].tolist(),model_revision=revision,matching_state='complete')
    reverse={str(c.pk):key for key,c in cases.items()}
    references=[r for r in records if r['role']=='reference'];queries=[r for r in records if r['role']=='query']
    details=[];probes=[];cpu_started=time.process_time()
    def score(a,b,mode):
        left=[indexes[p['text']] for p in versions[a]['representations'][mode]]
        right=[indexes[p['text']] for p in versions[b]['representations'][mode]]
        return float(np.max(vectors[left]@vectors[right].T)) if left and right else None
    with override_settings(SHADOW_RETRIEVAL_ENABLED=True):
        for q in queries:
            eligible=[r for r in references if r['institution']==q['institution']]
            started=time.perf_counter();found=discover(user,cases[q['id']],budget=20,reference_ids=[cases[r['id']].pk for r in eligible]);shadow_ms=(time.perf_counter()-started)*1000
            probes.append({'query':q['id'],'all_shadow_channels_ms':shadow_ms,'channel_fetch_and_count_ms':found['channel_fetch_and_count_ms'],
                'volumes':found['volumes'],'candidates':found['candidates'],'plans':found['plans']})
            convert=lambda ids:[reverse[x] for x in ids]
            methods={'production_summary_top5':convert(found['baseline']),
                'semantic_top20':convert(found['candidate_ids_by_channel']['semantic']),
                'lexical_top20':convert(found['candidate_ids_by_channel']['lexical']),
                'reference_top20':convert(found['candidate_ids_by_channel']['reference']),
                'hybrid_top5':convert(found['union'])}
            for mode in ['summary_selected_description','paragraphs']:
                scored=[(score(q['id'],r['id'],mode),r['id']) for r in eligible]
                methods[mode+'_top5']=[key for value,key in sorted((pair for pair in scored if pair[0] is not None),key=lambda pair:(-pair[0],pair[1]))[:5]]
            positive={r['id'] for r in eligible if labels.get((q['id'],r['id']))=='same_incident'}
            for method,ids in methods.items():
                judgments=[labels.get((q['id'],key)) for key in ids]
                if any(label is None for label in judgments):raise ValueError('Synthetic judgment coverage is incomplete.')
                details.append({'query':q['id'],'method':method,'returned':ids,'known_positive_count':len(positive),
                    'retrieved_relevant':[key for key,label in zip(ids,judgments) if label in ('same_incident','related_issue')],
                    'missed_same_incident':sorted(positive-set(ids)),
                    'false_suggestions':[key for key,label in zip(ids,judgments) if label=='unrelated'],
                    'threshold_abstained':not ids if method=='production_summary_top5' else None,
                    'top5_truncated':len(eligible)>5 and method.endswith('top5'),
                    'same_incident_hits':len(positive.intersection(ids)),'hits_at5':len(positive.intersection(ids[:5])),
                    'review_worthy':sum(label in ('same_incident','related_issue') for label in judgments),
                    'scope':'same genuine fixture institution; explicit synthetic IDs','shadow_all_channel_ms':shadow_ms,
                    'threshold_policy':'frozen production cutoff' if method=='production_summary_top5' else 'bounded experimental ranking; not calibrated for activation'})
    metrics={}
    for method in sorted({row['method'] for row in details}):
        rows=[r for r in details if r['method']==method];returned=sum(len(r['returned']) for r in rows);positive=sum(r['known_positive_count'] for r in rows)
        metrics[method]={'queries':len(rows),'returned':returned,'judgment_coverage':1 if returned else None,
            'candidate_recall':sum(r['same_incident_hits'] for r in rows)/positive if positive else None,
            'same_incident_recall_at5':sum(r['hits_at5'] for r in rows)/positive if positive else None,
            'review_worthy_precision':sum(r['review_worthy'] for r in rows)/returned if returned else None,
            'abstention_rate':sum(not r['returned'] for r in rows)/len(rows)}
    assert hashlib.file_digest(weights.open('rb'),'sha256').hexdigest()==before
    assert runtime()[1:]==(revision,cutoff)
    costs={}
    for mode in ['summary','summary_selected_description','paragraphs']:
        inputs=list(dict.fromkeys(part['text'] for version in versions.values() for part in version['representations'][mode]))
        started=time.perf_counter();model.encode(inputs,normalize_embeddings=True,batch_size=32)
        costs[mode]={'unique_inputs':len(inputs),'warm_encode_seconds':time.perf_counter()-started,'float32_vector_bytes':len(inputs)*384*4}
    np.savez_compressed(out/'experimental-embeddings.npz',vectors=vectors)
    (out/'representations.json').write_text(json.dumps(versions,indent=2),encoding='utf-8')
    report={'dataset_sha256':hashlib.sha256(raw).hexdigest(),'provenance':dataset['provenance'],'representation_policy':POLICY,
        'production_policy_changed':False,'model_revision':revision,'threshold':cutoff,'weights_sha256':before,
        'records':len(records),'queries':len(queries),'unique_passages_encoded':len(texts),'cold_load_seconds':load,'embedding_seconds':embedding_seconds,
        'comparison_cpu_seconds':time.process_time()-cpu_started,'process_peak_ram_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        'metrics':metrics,'queries_detail':details,'channel_probes':probes,'real_education_accuracy':None,
        'representation_costs':costs,'stored_compressed_vectors_bytes':(out/'experimental-embeddings.npz').stat().st_size,
        'limits':['Authored synthetic labels; no independent review.','Tiny source-selection diagnostic, not a model/policy promotion.','Experimental rankings use no newly calibrated threshold.','Paragraph max pooling can increase false positives.','Known-positive families exist only in this synthetic fixture.']}
    (out/'results.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    return report
