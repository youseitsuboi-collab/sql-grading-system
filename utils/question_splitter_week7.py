"""第7週用。第4週のフィールド抽出を継承し、見出し表記揺れに対応。"""
import re
from utils.question_splitter_week4 import (normalize_text, parse_query_block,
    extract_project_intent, extract_project_design, is_answered_project)

# 問題番号の独立見出し。「1：集計」「課題１」「問題1」「5：応用」など。
TOP = re.compile(r'^(?:(?:課題|問題|問|SQL)\s*([1-7])|([1-7]))\s*[:：.．、)）\-－]\s*(.*)$', re.I)
# 「5_3_1」「5_6_4」等。見出し行またはクエリー名に現れる番号。
QUERY_ID = re.compile(r'(?<!\d)(?:5|7)\s*[_－-]\s*([1-7])(?:\s*[_－-]\s*(\d{1,2}))?\s*[_－-]')
ALT_SUB = re.compile(r'^(?:SQL\s*([356])\s*[-－_]\s*(\d{1,2})|([356])\s*[.．]\s*(\d{1,2}))\s*[:：.．、)）\-－ ]', re.I)
TEMPLATE = re.compile(r'^\s*クエリー設計テンプレート\s*$')
QUERY_TITLE = re.compile(r'^(?:SPJ\s*クエリ[ー]?|集計\s*クエリ[ー]?|不一致\s*クエリ[ー]?|重複\s*クエリ[ー]?|ユニオン\s*クエリ[ー]?)\s*[:：]',re.I)

def _section_number(line):
    m=TOP.match(line.strip())
    if not m: return None
    n=int(m.group(1) or m.group(2))
    # 「3.1」「6.2」は補助番号。独立した問題見出しではない。
    if re.match(r'^\d+\s*[.．]\s*\d+',line.strip()): return None
    return n

def _split_sections(text):
    lines=normalize_text(text).splitlines()
    # 設計テンプレート以降を採点対象から除く
    for i,line in enumerate(lines):
        if TEMPLATE.match(line):
            lines=lines[:i];break
    headers=[]
    for i,line in enumerate(lines):
        n=_section_number(line)
        if n is not None:
            headers.append((i,n))
            continue
        # 「5.1：応用問題」「6.2：応用問題」は同じ問題の補助節
        m=re.match(r'^\s*([356])\s*[.．]\s*\d+\s*[:：]',line)
        if m: headers.append((i,int(m.group(1))))
    sections={}
    if headers:
        for j,(start,n) in enumerate(headers):
            end=headers[j+1][0] if j+1<len(headers) else len(lines)
            sections[n]=sections.get(n,'')+'\n'+'\n'.join(lines[start:end])
    else:
        # 独立した問題見出しがない場合、クエリー名に含まれる 5_1_ などを使用。
        markers=[]
        for i,line in enumerate(lines):
            if QUERY_TITLE.match(line.strip()):
                m=QUERY_ID.search(line)
                if m and not m.group(2): markers.append((i,int(m.group(1))))
        for j,(start,n) in enumerate(markers):
            end=markers[j+1][0] if j+1<len(markers) else len(lines)
            sections[n]=sections.get(n,'')+'\n'+'\n'.join(lines[start:end])
    return {n:s.strip() for n,s in sections.items()}

def _split_query_designs(block, n):
    """番号付き補助見出し、無番号のクエリー名、最終クエリーを分離する。"""
    lines = block.splitlines()
    markers = []
    for i, line in enumerate(lines):
        stripped = line.strip()
        # 5.1 / 6.2 / 7.3 の補助見出しを優先する
        helper = re.match(r'^([356])\s*[.．]\s*(\d{1,2})\s*[:：]?\s*(?:応用問題)?\s*$', stripped)
        if helper and int(helper.group(1)) == n:
            markers.append((i, int(helper.group(2)), 'helper'))
            continue
        if QUERY_TITLE.match(stripped) or re.match(r'^計クエリー\s*[:：]', stripped):
            match = QUERY_ID.search(stripped)
            subno = int(match.group(2)) if match and int(match.group(1)) == n and match.group(2) else None
            # 補助見出しの直後のクエリー名は同じ補助設計の一部
            if markers and markers[-1][2] == 'helper' and not any(
                QUERY_TITLE.match(x.strip()) or re.match(r'^計クエリー\s*[:：]',x.strip())
                for x in lines[markers[-1][0]+1:i]
            ):
                if subno is not None and markers[-1][1] != subno:
                    markers.append((i, subno, 'query'))
                continue
            markers.append((i, subno, 'query'))
    if not markers:
        return dict(parse_query_block(block), raw=block, subqueries={})
    # 3番は無番号の2つの集計クエリー、5・6番は番号付き補助クエリーと最終クエリー
    if n == 3:
        query_indices = [j for j, (_, _, kind) in enumerate(markers) if kind == 'query']
        if len(query_indices) >= 2:
            first = query_indices[0]
            markers[first] = (markers[first][0], 1, 'query')
    subs = {}
    mains = []
    for j, (start, subno, _) in enumerate(markers):
        end = markers[j+1][0] if j+1 < len(markers) else len(lines)
        raw = '\n'.join(lines[start:end]).strip()
        if not raw:
            continue
        if subno is not None:
            key = f'SQL{n}-{subno}'
            if key in subs:
                subs[key]['raw'] += '\n' + raw
                subs[key] = dict(parse_query_block(subs[key]['raw']), raw=subs[key]['raw'])
            else:
                subs[key] = dict(parse_query_block(raw), raw=raw)
        else:
            mains.append(raw)
    main_raw = '\n'.join(mains)
    return dict(parse_query_block(main_raw), raw=block, subqueries=subs)

def _project(raw,n):
    intent=extract_project_intent(raw)
    if not intent:
        m=re.search(r'(?m)^\s*(?:趣旨および求めるデータ|企画意図|趣旨)\s*[:：]?\s*$',raw)
        if m:
            tail=raw[m.end():]
            end=re.search(r'(?m)^\s*(?:設計|クエリー設計|SPJ\s*クエリー|集計\s*クエリー|不一致\s*クエリー)\s*[:：]?\s*',tail)
            intent=(tail[:end.start()] if end else tail).strip()
    design=extract_project_design(raw)
    if not design:
        m=re.search(r'(?m)^\s*(?:設計|SPJ\s*クエリー\s*[:：]|集計\s*クエリー\s*[:：])',raw)
        design=raw[m.start():] if m else ''
    answered=bool(raw) and (bool(intent) or is_answered_project(intent,design) or bool(re.search(r'(?im)^\s*SELECT\s+\S+',raw)))
    return {'type':'集計' if n==4 else '複数クエリー','intent':intent,
        'design':parse_query_block(design) if answered else {'fields':{}},
        'answered':answered,'raw':raw}

def split_week7_report(text):
    blocks=_split_sections(text)
    queries={}
    for n in (1,2,3,5,6):
        raw=blocks.get(n,'')
        if raw:
            queries[f'SQL{n}']=_split_query_designs(raw,n) if n in (3,5,6) else dict(parse_query_block(raw),raw=raw)
    projects={f'SQL{n}':_project(blocks.get(n,''),n) for n in (4,7)}
    return {'queries':queries,'projects':projects}
