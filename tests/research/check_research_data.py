"""Small deterministic checks for research-data parsing and leakage boundaries."""
import re
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from scripts.collect_training_data import synthetic
from scripts.audit_indian_complaints import sql_values,redact

def main():
 assert list(sql_values("('one\\'s text','hello, world',NULL,1);",0))==[["one's text",'hello, world',None,'1']]
 assert list(sql_values("('escaped ''quote''','line\\nnext');",0))==[["escaped 'quote'",'line\nnext']]
 try:list(sql_values('(NOW(),1);',0));raise AssertionError('SQL expressions must not be accepted.')
 except ValueError:pass
 cleaned=redact('Contact @student or example@test.invalid at https://example.invalid; call +91 98765 43210')
 assert '@student' not in cleaned and 'example@test.invalid' not in cleaned and '98765' not in cleaned
 data=synthetic();rows={r['id']:r for r in data['records']}
 groups={split:{r['template_group'] for r in rows.values() if r['split']==split} for split in ['train','validation','calibration','test']}
 assert len(data['pairs'])==1440 and len({r['family'] for r in rows.values()})==360
 assert all(not groups[a]&groups[b] for a in groups for b in groups if a!=b)
 assert all(rows[p['left']]['family']==rows[p['right']]['family'] and rows[p['left']]['split']==rows[p['right']]['split']==p['split'] for p in data['pairs'])
 print('Research parser, identifier redaction and family/template split checks passed.')
if __name__=='__main__':main()
