from openai import OpenAI
from utils.docx_reader import read_docx
from utils.question_splitter_spj import (
    split_by_spj_questions,
    split_answer_blocks,
    merge_questions_and_answers,
)
from utils.markdown_writer import to_markdown
from utils.markdown_reader import extract_q
import tempfile
import os
import re

QUESTIONS = {
    1: "SPJ質問1：政党名の一覧を求めよ．",
    2: "SPJ質問2：小選挙区で第10区を持つ都道府県の一覧を求めよ．",
    3: "SPJ質問3：12万票以上を獲得した候補者がいる小選挙区の一覧を求めよ．",
    4: "SPJ質問4：北海道ブロックにおける政党別の比例代表得票数を求め，多い順に表示せよ．",
    5: "SPJ質問5：東京都のいずれかの小選挙区に候補者を擁立している政党名を求めよ．",
    6: "SPJ質問6：国民民主党の立候補者一覧を求めよ．（小選挙区，比例代表のいずれかは問わない）",
    7: "SPJ質問7：参政党の立候補者一覧を求めよ．（比例代表立候補者のみ）",
    8: "SPJ質問8：東京ブロックで比例代表候補者を擁立している政党名を求めよ．",
}

def uploaded_docx_to_markdown(uploaded_bytes: bytes) -> str:
    # 一時ファイルは処理終了時に削除する（永続保存しない）
    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as tmp:
            tmp.write(uploaded_bytes)
            temp_path = tmp.name

        text = read_docx(temp_path)
        questions = split_by_spj_questions(text)
        answer_blocks = split_answer_blocks(text)
        merged = merge_questions_and_answers(questions, answer_blocks)
        return to_markdown(merged)
    finally:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)

def grade_markdown(student_md: str, model_md: str, api_key: str):
    client = OpenAI(api_key=api_key)
    results = []
    total_score = 0

    for q_num in range(1, 9):
        student_q = extract_q(student_md, q_num)
        model_q = extract_q(model_md, q_num)

        prompt = f"""
あなたは大学の情報システム科目を担当する教員です。
以下の学生回答を模範解答に基づいて採点してください。

【採点方針】
・評価項目ごとに ○ または × を付ける。
・学生回答と模範解答の表現が異なっていても，内容が意味的に同等であれば正解とする。
・模範解答と属性の記述順序が異なるだけで，意味や結果が同じ場合は誤りとしない。
・射影属性は，属性の順番が異なるだけであれば正解とする。
・並べ替え条件は，設問または模範解答に順序が明示されている場合のみ，その内容を厳密に評価する。
・結合条件は，必要なテーブル間の対応関係が正しく記述されているかを評価する。
・選択条件は，AND / OR を含め，設問で要求されている条件を満たしているかを評価する。
・重複除去が必要な設問については，射影属性またはクエリ設計として重複除去が適切に指定されているかを確認する。
・×の場合のみ理由を書く。
・理由は最後にまとめて書く。
・余計な説明は書かない。

【評価項目】
1 使用テーブル
2 結合条件
3 選択条件
4 射影属性
5 並べ替え条件

【設問】
{QUESTIONS[q_num]}

【学生回答】
{student_q}

【模範解答】
{model_q}

【出力形式】
使用テーブル：○ or ×
結合条件：○ or ×
選択条件：○ or ×
射影属性：○ or ×
並べ替え条件：○ or ×

合計点：X / 5

理由：
（×の項目のみ「項目名：理由」の形式で記述）
"""
        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
        )
        result_text = response.choices[0].message.content or ""
        m = re.search(r"合計点：\s*(\d+)\s*/\s*5", result_text)
        score = int(m.group(1)) if m else 0
        total_score += score
        results.append({"q_num": q_num, "score": score, "text": result_text})

    return results, total_score
