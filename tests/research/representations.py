"""Experimental literal passages; never write production complaint embeddings."""
import hashlib
import re

POLICY = 'literal-passages-v1'


def span(field, text, start, end):
    return {'field':field,'start':start,'end':end,'text':text[start:end],
            'source_digest':hashlib.sha256(text.encode('utf-8')).hexdigest()}


def passages(field, text, tokenizer, limit=256):
    if not isinstance(text,str) or not 8 <= limit <= 256: raise ValueError('Literal source text and a supported tokenizer limit are required.')
    result=[]
    for paragraph in re.finditer(r'\S[\s\S]*?(?=\n[ \t]*\n|\Z)',text):
        start,end=paragraph.span()
        while start < end:
            encoded=tokenizer.encode(text[start:end])
            if len(encoded.ids)<=limit:
                result.append(span(field,text,start,end));break
            offsets=[(a,b) for a,b in encoded.offsets if b>a]
            budget=limit-len(tokenizer.encode('').ids)
            stop=offsets[min(budget,len(offsets))-1][1]+start
            while len(tokenizer.encode(text[start:stop]).ids)>limit:
                stop-=1
            if stop<=start: raise ValueError('Tokenizer cannot produce a bounded source passage.')
            result.append(span(field,text,start,stop));start=stop
    return result


def representations(record, tokenizer, limit=256):
    summary,description=record['summary'],record['description']
    if not isinstance(summary,str) or not isinstance(description,str): raise ValueError('Original summary and description required.')
    a=[] if not summary.strip() or len(tokenizer.encode(summary).ids)>limit else [{'text':summary,'parts':[span('summary',summary,0,len(summary))]}]
    body=passages('description',description,tokenizer,limit)
    b=[]
    if a and body:
        first=body[0];selected=first['text']
        while selected and len(tokenizer.encode(summary+'\n'+selected).ids)>limit:
            ends=[end for start,end in tokenizer.encode(selected).offsets if end>start]
            selected=selected[:ends[-2]] if len(ends)>1 else ''
        if selected.strip():
            b=[{'text':summary+'\n'+selected,'parts':[span('summary',summary,0,len(summary)),span('description',description,first['start'],first['start']+len(selected))]}]
    c=[*a,*[{'text':p['text'],'parts':[p]} for p in body]]
    result={'summary':a,'summary_selected_description':b,'paragraphs':c}
    for items in result.values():
        for item in items:
            if len(tokenizer.encode(item['text']).ids)>limit: raise ValueError('Representation exceeds the explicit tokenizer limit.')
    return {'policy':POLICY,'limit':limit,'representations':result,
        'coverage':{'summary_available':bool(a),'selected_description_available':bool(b),
            'description_passages':len(body),'whole_description_in_combined_input':bool(b and b[0]['parts'][1]['text']==description)}}
