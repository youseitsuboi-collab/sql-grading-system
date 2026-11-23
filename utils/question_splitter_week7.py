"""第7週レポートの回答抽出。第4週の項目抽出関数を再利用する。"""
import re
from utils.question_splitter_week4 import normalize_text, parse_query_block, is_answered_project

HEADING = re.compile(r'(?m)^\s*([1-7])(?:\s*[.．]\s*([1-9]\d*))?\s*[:：]\s*(?:集計クエリー|応用問題|企画クエリー|SPJクエリー)?[^\n]*$')
QUERY = re.compile(r'(?m)^\s*(?:SPJ\s*クエリー|集計クエリー|不一致クエリー|ユニオンクエリー|重複クエリー)\s*[:：]\s*(?:[57]_)?([1-7])(?:_([1-9]\d*))?_[^\n]*$')
TEMPLATE = re.compile(r'(?m)^\s*クエリー設計テンプレート\s*$')

def _sections(text):
    text=normalize_text(text)
    marker=TEMPLATE.search(text)
    if marker: text=text[:marker.start()]
    headings=list(HEADING.finditer(text))
    sections={}
    for i,h in enumerate(headings):
        n=int(h.group(1)); sub=int(h.group(2)) if h.group(2) else None
        content=text[h.end():headings[i+1].start() if i+1<len(headings) else len(text)].strip()
        sections.setdefault((n,sub),[]).append(content)
    return sections

def _query_parts(text,n):
    matches=[m for m in QUERY.finditer(text) if int(m.group(1))==n]
    result=[]
    for i,m in enumerate(matches):
        raw=text[m.start():matches[i+1].start() if i+1<len(matches) else len(text)].strip()
        result.append((int(m.group(2)) if m.group(2) else None,raw))
    return result

def split_week7_report(text):
    sections=_sections(text)
    queries={}; projects={}
    for n in (1,2,3,5,6):
        candidates=[]
        for (section,sub),contents in sections.items():
            if section==n:
                for content in contents:
                    for parsed_sub,raw in _query_parts(content,n):
                        candidates.append((parsed_sub if parsed_sub is not None else sub,raw))
        if not candidates: continue
        if n in (3,5,6):
            subs={};main=None
            for sub,raw in candidates:
                obj=dict(parse_query_block(raw),raw=raw)
                if sub is None: main=obj
                else: subs[f'SQL{n}-{sub}']=obj
            if main is None: main={'fields':{},'raw':''}
            queries[f'SQL{n}']=dict(main,subqueries=subs,raw='\n'.join(x[1] for x in candidates))
        else:
            queries[f'SQL{n}']=dict(parse_query_block(candidates[-1][1]),raw=candidates[-1][1])
    for n in (4,7):
        raw='\n'.join(s for (num,_),contents in sections.items() if num==n for s in contents).strip()
        parts=_query_parts(raw,n)
        intro=raw[:raw.find(parts[0][1])] if parts else raw
        intent_match=re.search(r'(?:趣旨および求めるデータ|企画意図|\[趣旨\]|【趣旨】)\s*[:：]?\s*',intro)
        intent=intro[intent_match.end():].strip() if intent_match else ''
        intent=re.sub(r'(?m)^\s*設計\s*$', '',intent).strip()
        design_text='\n'.join(p for _,p in parts)
        answered=bool(intent or parts or (design_text and is_answered_project('',design_text)))
        projects[f'SQL{n}']={'type':'集計' if n==4 else '複数クエリー', 'intent':intent,
            'design':parse_query_block(design_text) if answered else {'fields':{}},
            'answered':answered,'raw':raw,'subqueries':{f'SQL{n}-{s}':dict(parse_query_block(p),raw=p) for s,p in parts if s is not None}}
    return {'queries':queries,'projects':projects}
