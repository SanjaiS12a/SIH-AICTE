"""Read-only warm CPU encoding measurement, separate from broker and SQL time."""
import hashlib
import json
import resource
import statistics
import time
from pathlib import Path
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import connection
from cases.models import Complaint
from cases.matching import runtime, encoder, tokenizer


class Command(BaseCommand):
    help = 'Measure 1k/10k synthetic summaries in an isolated scale database without changing vectors.'

    def add_arguments(self,parser):
        parser.add_argument('--output',required=True)

    def handle(self,*args,**options):
        if not connection.settings_dict['NAME'].startswith('coordination_scale_'):
            raise CommandError('Requires an isolated scale database.')
        target=Path(options['output']).resolve()
        if not target.is_relative_to((settings.RESULTS_DIR/'runs').resolve()) or target.exists():
            raise CommandError('Use a new ignored run output.')
        texts=list(Complaint.objects.filter(source_system='synthetic-benchmark',matching_state='complete').order_by('source_reference').values_list('summary',flat=True)[:10000])
        if len(texts)!=10000:raise CommandError('Requires 10,000 completed synthetic benchmark records.')
        path,revision,cutoff=runtime()
        expected=json.loads((Path(__file__).resolve().parents[3]/'model-manifest.json').read_text())
        with (Path(path)/'model.safetensors').open('rb') as stream:
            if hashlib.file_digest(stream,'sha256').hexdigest()!=expected['weights_sha256'] or revision!=expected['revision']:
                raise CommandError('Pinned model does not match.')
        model_tokenizer=tokenizer()
        counts=[len(model_tokenizer.encode(text).ids) for text in texts]
        assert all(0<n<=256 for n in counts),'No silent truncation allowed'
        started=time.perf_counter();model=encoder();cold=time.perf_counter()-started
        model.encode(['Synthetic warm-up outside measured corpus.'],normalize_embeddings=True)
        results=[]
        for count in [1000,10000]:
            timings=[];started=time.perf_counter()
            for offset in range(0,count,32):
                began=time.perf_counter();vectors=model.encode(texts[offset:min(offset+32,count)],normalize_embeddings=True,batch_size=32)
                timings.append((time.perf_counter()-began)*1000)
                assert vectors.shape==(min(32,count-offset),384)
                assert abs(sum(float(v)*float(v) for v in vectors[0])-1)<.001
            seconds=time.perf_counter()-started
            results.append({'records':count,'seconds':seconds,'summaries_per_second':count/seconds,
                'batch_p95_ms':sorted(timings)[int(.95*len(timings))], 'mean_wordpieces':statistics.mean(counts[:count]),'max_wordpieces':max(counts[:count])})
        result={'device':'cpu','torch_threads':2,'model_revision':revision,'threshold':cutoff,'weights_sha256':expected['weights_sha256'],
            'cold_model_load_seconds':cold,'cold_scope':'Dependency imports and local model construction; checksum and corpus fetch excluded.',
            'results':results,'database_writes':False,'peak_process_rss_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,
            'limit':'Standalone warm batches of realistic-length synthetic summaries; excludes queue, matching SQL and HTTP. No accuracy claim.'}
        target.parent.mkdir(parents=True,exist_ok=True)
        with target.open('x',encoding='utf-8') as stream:json.dump(result,stream,indent=2)
        self.stdout.write(json.dumps(result))
