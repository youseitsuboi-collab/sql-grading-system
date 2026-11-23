"""第7週採点。第4週の評価規則・企画採点を再利用し、第4週のファイルは変更しない。"""
import json
from pathlib import Path
from week4_grader import (grade_standard_query, grade_complex_query, grade_project_query,
    load_er_schema, load_existing_queries, call_gpt_json, normalize_grade, SCORE_MAP, sanitize_reason)

MODEL_PATH=Path(__file__).resolve().parent/'data/model/week7_model_2026.json'
FIELDS=('使用テーブル','結合条件','選択条件（集計前）','行見出し','集計方法','射影属性','並べ替え条件')

def _zero(name, fields):
    items=[{'item':f,'answer':'','grade':'×','score':0,'reason':'回答がないため。'} for f in fields]
    return {'sql':name,'score':0,'max_score':len(items),'items':items}

AGG_FIELDS=('使用テーブル','結合条件','選択条件（集計前）','行見出し','列見出し','集計方法','選択条件（集計後）','射影属性','並べ替え条件')

def grade_problem3(answer):
    # 教員の模範設計なし。補助と最終の9項目ずつ、18点満点で固定。
    sections=[]
    sub=(answer or {}).get('subqueries',{}).get('SQL3-1',{})
    for label,part in [('SQL3-1',sub),('最終クエリー',answer or {})]:
        fields=part.get('fields',{})
        for field in AGG_FIELDS:
            sections.append((f'{label}：{field}',str(fields.get(field,''))))
    if not any(value.strip() for _,value in sections):
        return _zero('SQL3',[name for name,_ in sections])
    prompt='大学のSQL設計レポートを採点する。課題は「立候補者数毎に小選挙区数を集計せよ」。固定模範解答はない。県名と選挙区ごとの候補者数を集計し、その人数ごとの小選挙区数を集計できるか検証する。各項目を目的に照らして○=1点、△=0.5点、×=0点で採点。別の妥当な設計も認める。「なし」が適切な項目は○としてよい。空欄は必ず×。記載されていない処理を推測しない。JSON {"items":[{"item":"項目名","grade":"○","reason":"理由"}]}を返す。項目名は入力と完全一致。'
    response=call_gpt_json(prompt,json.dumps({'課題':'立候補者数毎に小選挙区数を集計','学生の回答':answer,
        '評価項目':[{'item':k,'answer':v} for k,v in sections]},ensure_ascii=False))
    grades={x.get('item'):x for x in response.get('items',[]) if isinstance(x,dict)}
    items=[]
    for key,value in sections:
        item=grades.get(key,{})
        grade=normalize_grade(item.get('grade','×')) if value.strip() else '×'
        items.append({'item':key,'answer':value,'grade':grade,'score':SCORE_MAP[grade],
            'reason':sanitize_reason(item.get('reason','回答がないため。' if not value.strip() else '評価を取得できませんでした。'))})
    return {'sql':'SQL3','score':sum(i['score'] for i in items),'max_score':len(items),'items':items}

def grade_week7(parsed_report):
    models=json.loads(MODEL_PATH.read_text(encoding='utf-8'))
    answers=parsed_report.get('queries',{})
    results={}
    for n in (1,2,3,5,6):
        key=f'SQL{n}'; answer=answers.get(key)
        if n==3: result=grade_problem3(answer)
        elif models[key].get('subqueries'): result=grade_complex_query(key,models[key],answer)
        else: result=grade_standard_query(key,models[key],answer)
        results[key]=result
    er=load_er_schema()
    existing=load_existing_queries()
    projects={}
    for n in (4,7):
        key=f'SQL{n}'; ans=parsed_report.get('projects',{}).get(key)
        # 第4週の企画採点に課題固有の制約を明示する。第4週採点器のコードは変更しない。
        if ans and ans.get('answered'):
            ans=dict(ans)
            condition=('集計クエリーであること。' if n==4 else
                '複数のクエリーを組み合わせ、単純な単一クエリーでは代替しにくいこと。')
            ans['raw']=ans.get('raw','')+'\n【採点者向け課題要件】'+condition
        projects[key]=grade_project_query(key,ans,er,existing)
    qscore=sum(x['score'] for x in results.values());qmax=sum(x['max_score'] for x in results.values())
    pscore=sum(x['total_score'] for x in projects.values())
    return {'queries':results,'projects':projects,'query_score':qscore,'query_max':qmax,
        'project_score':pscore,'project_max':30,'total_score':qscore+pscore,'max_score':qmax+30}
