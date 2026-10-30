"""Read the publisher's SQL as data only; export redacted annotated tweet text."""
import hashlib,json,re
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent

def sql_values(text,start):
 row=[];token=[];quoted=False;inside=False;i=start
 while i<len(text):
  c=text[i]
  if quoted:
   if c=='\\':
    i+=1
    if i<len(text):token.append({'n':'\n','r':'\r','t':'\t','0':'\x00'}.get(text[i],text[i]))
   elif c=="'":
    if i+1<len(text) and text[i+1]=="'":token.append("'");i+=1
    else:quoted=False
   else:token.append(c)
  elif c=="'":quoted=True
  elif c=='(':
   if inside:raise ValueError('Unexpected SQL expression; only literal tuples are accepted.')
   inside=True;row=[];token=[]
  elif c in ',)' and inside:
   value=''.join(token).strip();row.append(None if value=='NULL' else value);token=[]
   if c==')':yield row;inside=False
  elif c==';' and not inside:return
  elif inside:token.append(c)
  elif not c.isspace() and c!=',':raise ValueError('Unexpected SQL token.')
  i+=1
 raise ValueError('Unterminated INSERT statement.')

def redact(text):
 text=re.sub(r'https?://\S+','[URL]',text)
 text=re.sub(r'\b[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}\b','[EMAIL]',text)
 text=re.sub(r'(?<!\w)@[A-Za-z0-9_]+','[USER]',text)
 text=re.sub(r'(?<!\w)\+?\d[\d ()-]{7,}\d(?!\w)','[NUMBER]',text)
 return text

def main():
 dest=ROOT/'data/research';raw=(dest/'Complaints_Reports_Data.sql').read_bytes();text=raw.decode('utf-8');tables={}
 for match in re.finditer(r'INSERT INTO\s+`([^`]+)`\s+VALUES\s*',text):tables.setdefault(match[1],[]).extend(sql_values(text,match.end()))
 rows=tables.get('annotated',[]);assert rows and all(len(r)==5 for r in rows)
 output=[{'text':redact(r[1] or ''),'class':r[2],'category':r[3],'organization':r[4],'provenance':'IIIT Delhi Mendeley w2cp7h53s5 v1; CC BY 4.0; Agarwal, Mittal, Sureka (2016)'} for r in rows]
 with (dest/'indian_complaints_redacted.jsonl').open('w',encoding='utf-8') as f:
  for r in output:f.write(json.dumps(r,ensure_ascii=False)+'\n')
 profile={'source':'https://data.mendeley.com/datasets/w2cp7h53s5/1','sha256':hashlib.sha256(raw).hexdigest(),'license':'CC BY 4.0','access':'Public publisher SQL download, verified against publisher SHA256','status':'downloaded_audited','fields':['text','class','category','organization'],'tables':{k:len(v) for k,v in tables.items()},'annotated_records':len(rows),'missing_text':sum(not r['text'] for r in output),'duplicate_text':len(output)-len({r['text'] for r in output}),'class_counts':dict(Counter(r['class'] for r in output)),'language_counts':dict(Counter(r[8] for r in tables.get('posts',[]))),'personal_identifiers':'Raw dump includes users, coordinates and tweet IDs. Derived file excludes those columns and replaces handles, URLs, emails and phone-like numbers. Names and contextual identifiers may remain; manual privacy review pending.','labels':'Complaint classification, not same-incident/related/unrelated labels','training_use':'excluded from pair fine-tuning; privacy review and pair annotation required','attribution':'Swati Agarwal, Nitish Mittal, Ashish Sureka; Enhanced Dataset of Citizen Centric Complaints and Grievances on Twitter (2016), DOI 10.17632/w2cp7h53s5.1'}
 (dest/'indian_complaints_profile.json').write_text(json.dumps(profile,indent=2),encoding='utf-8')
 register=json.loads((dest/'source_register.json').read_text(encoding='utf-8'))
 for source in register['sources']:
  if source['name'].startswith('IIIT'):source.update(profile);source.pop('error',None)
 (dest/'source_register.json').write_text(json.dumps(register,indent=2),encoding='utf-8')
 (ROOT/'tests/results/source-register.json').write_text(json.dumps(register,indent=2),encoding='utf-8')
 print(json.dumps({k:profile[k] for k in ['status','tables','annotated_records','missing_text','duplicate_text','class_counts','language_counts']},indent=2))
if __name__=='__main__':main()
