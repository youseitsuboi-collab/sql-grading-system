"""情報システム実験・第7週 Streamlit採点画面"""
import csv, io, os, tempfile, zipfile
from pathlib import Path
import streamlit as st
from utils.docx_reader import read_docx
from utils.question_splitter_week7 import split_week7_report
from week7_grader import grade_week7

st.set_page_config(page_title='情報システム実験 第7週 採点システム',page_icon='📝',layout='wide')
st.title('情報システム実験 第7週 採点システム')
st.caption('問題1・2・3・5・6：設計採点／問題4・7：企画採点。複数のWordレポートに対応。')

def result_files(result, parsed):
    output=io.StringIO();writer=csv.writer(output)
    writer.writerow(['問題','評価項目','回答','判定','点数','理由'])
    lines=['情報システム実験 第7週 採点結果','='*45]
    for key,r in result['queries'].items():
        lines.append(f'\n【{key}】 {r["score"]} / {r["max_score"]}点')
        for item in r['items']:
            vals=[key,item['item'],item.get('answer',''),item['grade'],item['score'],item['reason']]
            writer.writerow(vals);lines.append(f'{vals[3]} {vals[1]} [{vals[4]}点]\n 回答：{vals[2] or "（未回答）"}\n 理由：{vals[5]}')
    for key,r in result['projects'].items():
        lines.append(f'\n【{key} 企画】 {r["total_score"]} / 15点')
        for code,label in [('validity','妥当性'),('originality','オリジナリティ'),('usefulness','有用性')]:
            data=r.get(code,{})
            writer.writerow([key,label,'','',data.get('score',0),data.get('reason','')])
            lines.append(f'{label}: {data.get("score",0)}/5点\n 理由：{data.get("reason","")}')
    lines.append(f'\n総合得点：{result["total_score"]} / {result["max_score"]}点')
    return output.getvalue().encode('utf-8-sig'),'\n'.join(lines).encode('utf-8-sig')

uploads=st.file_uploader('Wordレポートを選択（複数選択可）',type=['docx'],accept_multiple_files=True)
if uploads and st.button('採点開始', type='primary'):
    results = {}
    errors = {}
    progress = st.progress(0, text=f'採点準備中（0/{len(uploads)}件）')
    with st.status('🔄 採点中です。しばらくお待ちください…', expanded=True) as status:
        current_file = st.empty()
        for i, upload in enumerate(uploads):
            current_file.info(f'採点中：{upload.name}（{i + 1}/{len(uploads)}件）')
            tmp = None
            try:
                with tempfile.NamedTemporaryFile(delete=False, suffix='.docx') as f:
                    f.write(upload.getbuffer())
                    tmp = f.name
                parsed = split_week7_report(read_docx(tmp))
                if not parsed.get('queries'):
                    raise ValueError('問題1・2・3・5・6の回答を1件も抽出できませんでした。採点せず停止しました。Wordの見出し形式を確認してください。')
                results[upload.name] = (grade_week7(parsed), parsed)
            except Exception as exc:
                errors[upload.name] = str(exc)
            finally:
                if tmp and os.path.exists(tmp):
                    os.remove(tmp)
                progress.progress((i + 1) / len(uploads), text=f'採点進捗：{i + 1}/{len(uploads)}件')
        current_file.empty()
        st.session_state['week7_results'] = results
        st.session_state['week7_errors'] = errors
        if errors:
            status.update(label=f'⚠️ 採点処理が終了しました（成功：{len(results)}件／エラー：{len(errors)}件）', state='error', expanded=False)
        else:
            status.update(label=f'✅ 採点が完了しました！（{len(results)}件）', state='complete', expanded=False)

for name,error in st.session_state.get('week7_errors',{}).items():
    st.error(f'{name}：{error}')
results=st.session_state.get('week7_results',{})
if results:
    name=st.selectbox('採点結果を表示するファイル',list(results))
    result,parsed=results[name]
    a,b,c=st.columns(3)
    a.metric('設計問題',f'{result["query_score"]}/{result["query_max"]}点')
    b.metric('企画問題',f'{result["project_score"]}/30点')
    c.metric('合計',f'{result["total_score"]}/{result["max_score"]}点')
    for key,r in result['queries'].items():
        with st.expander(f'{key}　{r["score"]}/{r["max_score"]}点'):
            for item in r['items']:
                st.markdown(f'**{item["grade"]} {item["item"]} [{item["score"]}点]**')
                st.write('回答：',item.get('answer','') or '（未回答）')
                st.write('理由：',item.get('reason',''))
    for key,r in result['projects'].items():
        with st.expander(f'{key}（企画） {r["total_score"]}/15点'):
            for code,label in [('validity','妥当性'),('originality','オリジナリティ'),('usefulness','有用性')]:
                data=r.get(code,{})
                st.markdown(f'**{label}：{data.get("score",0)}/5点**')
                st.write(data.get('reason',''))
    csvdata,txtdata=result_files(result,parsed)
    left,right=st.columns(2)
    left.download_button('CSVダウンロード',csvdata,file_name=Path(name).stem+'_result.csv',mime='text/csv')
    right.download_button('TXTダウンロード',txtdata,file_name=Path(name).stem+'_result.txt',mime='text/plain')
    buf=io.BytesIO()
    with zipfile.ZipFile(buf,'w',zipfile.ZIP_DEFLATED) as z:
        for filename,(r,p) in results.items():
            _,txt=result_files(r,p)
            z.writestr(Path(filename).stem+'_result.txt',txt)
    st.download_button('全件ZIPダウンロード',buf.getvalue(),file_name='week7_grading_results.zip',mime='application/zip')
