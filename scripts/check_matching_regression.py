"""Check frozen candidates on the original synthetic benchmark without recalibration."""
import json
from pathlib import Path
import torch
from sentence_transformers import SentenceTransformer
from train_matching import evaluate,vectors
ROOT=Path(__file__).resolve().parent.parent

def main():
 torch.set_num_threads(2)
 report=json.loads((ROOT/'reports/training.json').read_text(encoding='utf-8'))
 old=json.loads((ROOT/'data/evaluation.json').read_text(encoding='utf-8'))
 rows=[r for r in old['records'] if r['split']=='test']
 result={'source':'Original authored synthetic benchmark; regression only, not new held-out evidence. Original test reference corpus preserved. No threshold changes.','models':{}}
 for name in ['baseline',report['candidate_selected_on_validation']]:
  variant=report['variants'][name];model=SentenceTransformer(variant['path'],device='cpu',local_files_only=True)
  threshold=json.loads((ROOT/'backend/calibration.json').read_text())['threshold'] if name=='baseline' else variant['calibration']['threshold']
  result['models'][name]=evaluate(vectors(model,rows),rows,old['pairs'],'test',threshold)
 report['regression']=result
 (ROOT/'reports/training-regression.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
 (ROOT/'reports/training.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
 (Path(report['run'])/'experiment.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
 print(json.dumps(result,indent=2))
if __name__=='__main__':main()
