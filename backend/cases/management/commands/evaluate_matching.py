import json
import platform
import time
from pathlib import Path
import numpy as np
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from sklearn.feature_extraction.text import TfidfVectorizer
from cases.matching import encoder, revision

def metrics(scores, labels, threshold):
    predicted = scores >= threshold
    positive = labels.astype(bool)
    tp = int(np.sum(predicted & positive)); fp = int(np.sum(predicted & ~positive)); fn = int(np.sum(~predicted & positive))
    p = tp/(tp+fp) if tp+fp else 0
    r = tp/(tp+fn) if tp+fn else 0
    return {'precision':p, 'recall':r, 'f1':2*p*r/(p+r) if p+r else 0, 'tp':tp,'fp':fp,'fn':fn}

def calibrate(scores, labels):
    candidates = [(float(t),metrics(scores,labels,float(t))) for t in np.unique(scores)]
    valid = [x for x in candidates if x[1]['precision'] >= .85]
    return max(valid, key=lambda x:(x[1]['f1'],x[1]['recall'],x[0])) if valid else None

class Command(BaseCommand):
    help = 'Calibrate on incident-separated synthetic labels and evaluate a frozen threshold on held-out families.'
    def add_arguments(self,parser):
        parser.add_argument('--data',default=str(settings.BASE_DIR.parent/'data'/'evaluation.json'))
        parser.add_argument('--output',default=str(settings.RESULTS_DIR/'matching.json'))
    def handle(self,*args,**options):
        corpus = json.loads(Path(options['data']).read_text(encoding='utf-8'))
        rows,pairs=corpus['records'],corpus['pairs']
        families={split:{r['family'] for r in rows if r['split']==split} for split in ['calibration','test']}
        assert not families['calibration'] & families['test']
        index={r['id']:i for i,r in enumerate(rows)}
        texts=[r['text'] for r in rows]
        started=time.perf_counter(); model=encoder(); cold=time.perf_counter()-started
        started=time.perf_counter(); dense=model.encode(texts,normalize_embeddings=True,batch_size=32); elapsed=time.perf_counter()-started
        fit_texts=[r['text'] for r in rows if r['split']=='calibration']
        tfidf=TfidfVectorizer(ngram_range=(1,2)).fit(fit_texts).transform(texts)
        output={'model_revision':revision(),'label_provenance':corpus['label_provenance'],
                'limits':'Synthetic scenario labels, not independent human validation or real-world accuracy.',
                'cold_load_seconds':cold,'embedding_seconds':elapsed,'records':len(rows),
                'hardware':{'platform':platform.platform(),'processor':platform.processor()},'models':{}}
        for name,matrix in [('tfidf',tfidf),('minilm',dense)]:
            scores=np.array([float((matrix[index[p['left']]] @ matrix[index[p['right']]].T).toarray()[0,0]) if name=='tfidf' else float(matrix[index[p['left']]] @ matrix[index[p['right']]]) for p in pairs])
            labels=np.array([p['label'] in ('same_incident','related_issue') for p in pairs])
            calibration=np.array([p['split']=='calibration' for p in pairs])
            choice=calibrate(scores[calibration],labels[calibration])
            if choice is None:
                output['models'][name]={'calibration_passed':False};continue
            threshold,cal_metrics=choice
            test_metrics=metrics(scores[~calibration],labels[~calibration],threshold)
            hits=[]
            for query in corpus['retrieval']:
                if query['split']!='test':continue
                row=rows[index[query['query']]]
                candidates=[r for r in rows if r['split']=='test' and r['institution']==row['institution'] and not r['id'].endswith('-b')]
                def similarity(other):
                    a,b=index[query['query']],index[other['id']]
                    return float((matrix[a]@matrix[b].T).toarray()[0,0]) if name=='tfidf' else float(matrix[a]@matrix[b])
                top=sorted(candidates,key=similarity,reverse=True)[:5]
                hits.append(bool(set(query['relevant']) & {r['id'] for r in top}))
            output['models'][name]={'threshold':threshold,'calibration':cal_metrics,'held_out_test':test_metrics,'recall_at_5':sum(hits)/len(hits),'test_queries':len(hits),'calibration_passed':True}
        result=output['models'].get('minilm',{})
        if result.get('calibration_passed'):
            (settings.BASE_DIR/'calibration.json').write_text(json.dumps({'threshold':result['threshold'],'model_revision':revision(),'source':'synthetic calibration; human review pending'},indent=2),encoding='utf-8')
        dest=Path(options['output']);dest.parent.mkdir(parents=True,exist_ok=True);dest.write_text(json.dumps(output,indent=2),encoding='utf-8')
        self.stdout.write(json.dumps(output,indent=2))
