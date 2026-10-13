import json
from openai import OpenAI


# ============================================================
# OpenAI
# ============================================================

client = OpenAI()


# ============================================================
# 設定
# ============================================================

MODEL_ANSWER_PATH = "data/model/week4_model_2026.json"

SCORE_MAP = {
    "○": 1.0,
    "△": 0.5,
    "×": 0.0
}


# ============================================================
# 模範解答読み込み
# ============================================================

def load_model_answers():
    with open(
        MODEL_ANSWER_PATH,
        "r",
        encoding="utf-8"
    ) as f:
        return json.load(f)


# ============================================================
# GPT共通処理
# ============================================================

def call_gpt_json(system_prompt, user_prompt):

    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        temperature=0,
        response_format={
            "type": "json_object"
        },
        messages=[
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": user_prompt
            }
        ]
    )

    content = response.choices[0].message.content

    return json.loads(content)


# ============================================================
# 共通採点ルール
# ============================================================

COMMON_RULES = """
あなたは大学の情報システム実験における
SQLクエリ設計レポートの採点者です。

教員が作成した模範解答と学生の回答を比較し、
各評価項目を「○」「△」「×」の3段階で評価してください。


【採点基準】

○ = 1点
必要な内容をすべて満たしている。

△ = 0.5点
必要な内容の一部は正しいが、
一部に不足または誤りがある。

× = 0点
必要な内容を満たしていない。
または未回答である。


【最重要ルール】

1. 教員が作成した模範解答は絶対的な正解とする。

2. 模範解答に誤りや不自然な点があるように見えても、
   模範解答を訂正、変更、批判してはならない。

3. 完全な文字列一致は要求しない。
   表記ゆれ、全角半角、記号、語順などが異なっていても、
   意味が完全に同等なら○とする。

4. SQL関数などの意味的に同等な表現も○とする。

   例：
   「得票数の最大」
   「MAX(得票数)」

   は意味が同等なので○。

5. 必要な内容の一部だけが記述されている場合は△とする。

   例：
   必要な内容：
   「県名、選挙区」

   回答：
   「県名」

   この場合は△。

6. 必要な複数のテーブルの一部だけが
   指定されている場合も△とする。

7. 必要な複数の条件の一部だけが
   正しく記述されている場合も△とする。

8. 必要な内容とは異なる内容しか
   記述されていない場合は×とする。

9. 未回答、空欄、対応する記述が存在しない場合は×とする。

10. 学生が書いていない内容を推測して補ってはならない。

11. 他の評価項目に書かれている内容を、
    評価中の項目に書かれているものとして
    勝手に移動してはならない。

12. 模範解答に存在しない余分な内容が追加されていても、
    結果や意味に影響しない場合は、それだけを理由に×にしない。

13. 余分な内容によって結果や意味が変化する場合は、
    その影響の程度に応じて△または×とする。

14. ○は「完全または意味的に完全に正しい場合」に限る。

15. △は「部分的に正しい場合」に限る。

16. 全く異なる内容を、関連しているという理由だけで
    △にしてはならない。

17. 判定理由には模範解答そのものを掲載しないこと。

18. reasonには学生の回答について、
    なぜ○、△、×なのかを簡潔に記述すること。

19. reasonに「模範解答では～」など、
    模範解答の内容を直接表示する説明を書かないこと。

20. gradeとreasonを必ず一致させること。

    ○の場合：
    不足や誤りを指摘してはならない。

    △の場合：
    何が部分的に正しく、
    何が不足または誤っているかを説明する。

    ×の場合：
    必要な内容を満たしていない理由を説明する。
    
21. △は、必要な内容を構成する意味要素の一部を
    正しく記述している場合に限る。

22. 単に関連する属性名、条件、キーワードが
    含まれているだけでは△にしてはならない。

23. 必要な処理そのものが指定されていない場合は×とする。

    例：
    必要：MAX(得票数)
    回答：得票数
    → ×
    理由：集計対象の属性だけであり、
    集計方法が指定されていない。

24. 必要な処理とは異なる処理が指定されている場合は×とする。

    例：
    必要：MAX(得票数)
    回答：SUM(得票数)
    → ×

25. 必要な条件が存在するのに、
    回答が「なし」の場合は×とする。
    これは部分的に正しい回答ではないため△にしない。

26. 必要な内容が複数の要素から構成され、
    そのうち一部を正しく記述している場合は△とする。

    例：
    必要：県名、選挙区
    回答：県名
    → △

    必要：テーブルA、テーブルB、テーブルC
    回答：テーブルA、テーブルB
    → △

    必要：結合条件A、結合条件B
    回答：結合条件A
    → △

27. 正しい内容を別の欄に記述している場合は、
    内容そのものは理解している可能性があるため△とする。
    ただし、正しい欄に記述されているものとして○にはしない。

28. サブクエリそのものが存在しない場合は、
    他のクエリに似た内容が存在しても、
    そのサブクエリの評価項目は×とする。

29. reasonでは「模範解答」という語を使用しないこと。
31. reasonは学生本人に提示するフィードバックである。
32. reasonでは「模範解答」「正解例」「教員の解答」など、採点基準となる解答の存在を示す表現を使用してはならない。
33. 「模範解答と異なるため」のような理由は禁止する。学生の回答そのものについて、何が不足・余分・不適切なのかだけを説明すること。
34. reasonでは、正しい答えそのものを必要以上に開示しないこと。
35. 例：「模範解答と異なるため」ではなく、「必要な内容に加えて余分な属性が含まれているため」のように説明すること。

30. reasonでは正解内容そのものを学生に開示しないこと。
    不足している内容についても、必要以上に具体的な
    正解内容を提示しないこと。
"""


# ============================================================
# GPTの評価記号を安全に処理
# ============================================================

def sanitize_reason(reason):
    """学生向けフィードバックに採点基準の内部表現を出さない。"""
    reason = str(reason or "").strip()

    if not reason:
        return "判定理由を取得できなかったため。"

    forbidden_words = [
        "模範解答",
        "正解例",
        "教員の解答",
    ]

    if any(word in reason for word in forbidden_words):
        return "回答内容の一部が採点基準を満たしていないため。"

    return reason


def normalize_grade(grade):

    if grade in SCORE_MAP:
        return grade

    return "×"


# ============================================================
# SQL1～SQL6
# ============================================================

def grade_standard_query(
    sql_name,
    model_answer,
    student_answer
):

    model_fields = model_answer.get(
        "fields",
        {}
    )

    # --------------------------------------------------------
    # SQL全体が未回答
    # --------------------------------------------------------

    if not student_answer:

        results = []

        for field in model_fields:

            results.append({
                "item": field,
                "answer": "",
                "grade": "×",
                "score": 0.0,
                "reason": "回答がないため。"
            })

        return {
            "sql": sql_name,
            "score": 0.0,
            "max_score": len(model_fields),
            "items": results
        }

    student_fields = student_answer.get(
        "fields",
        {}
    )

    # --------------------------------------------------------
    # GPT採点
    # --------------------------------------------------------

    system_prompt = COMMON_RULES + """

【通常クエリの採点】

模範解答の各評価項目と、
学生回答の同じ評価項目を比較してください。

別の評価項目に正しい内容が記述されていても、
評価中の項目の回答として扱わないでください。


【出力形式】

必ず次のJSON形式だけを返してください。

{
  "items": [
    {
      "item": "評価項目名",
      "grade": "○",
      "reason": "簡潔な理由"
    }
  ]
}

gradeには必ず
「○」「△」「×」
のいずれか1つだけを指定してください。

itemの名称は変更しないでください。
"""

    user_prompt = f"""
採点対象：
{sql_name}

【教員の模範解答】

{json.dumps(
    model_fields,
    ensure_ascii=False,
    indent=2
)}

【学生の回答】

{json.dumps(
    student_fields,
    ensure_ascii=False,
    indent=2
)}

模範解答に存在するすべての評価項目を、
1項目ずつ○、△、×で判定してください。
"""

    gpt_result = call_gpt_json(
        system_prompt,
        user_prompt
    )

    gpt_items = {}

    for item in gpt_result.get(
        "items",
        []
    ):

        item_name = item.get(
            "item",
            ""
        )

        if item_name:
            gpt_items[item_name] = item

    # --------------------------------------------------------
    # Python側で結果確定
    # --------------------------------------------------------

    results = []
    total_score = 0.0

    for field in model_fields:

        student_value = student_fields.get(
            field,
            ""
        )

        # 空欄は必ず×
        if not str(student_value).strip():

            grade = "×"
            reason = "回答がないため。"

        else:

            gpt_item = gpt_items.get(
                field,
                {}
            )

            grade = normalize_grade(
                gpt_item.get(
                    "grade",
                    "×"
                )
            )

            reason = sanitize_reason(
                gpt_item.get(
                    "reason",
                    "判定結果を取得できなかったため。"
                )
            )

        score = SCORE_MAP[grade]

        total_score += score

        results.append({
            "item": field,
            "answer": student_value,
            "grade": grade,
            "score": score,
            "reason": reason
        })

    return {
        "sql": sql_name,
        "score": total_score,
        "max_score": len(model_fields),
        "items": results
    }


# ============================================================
# SQL7・SQL8
# ============================================================

def grade_complex_query(
    sql_name,
    model_answer,
    student_answer
):

    evaluation_items = []

    # --------------------------------------------------------
    # サブクエリ
    # --------------------------------------------------------

    subqueries = model_answer.get(
        "subqueries",
        {}
    )

    for subquery_name, subquery_data in subqueries.items():

        sub_fields = subquery_data.get(
            "fields",
            {}
        )

        for field, answer in sub_fields.items():

            evaluation_items.append({
                "item": f"{subquery_name}：{field}",
                "model_answer": answer,
                "location": subquery_name,
                "field": field
            })

    # --------------------------------------------------------
    # 最終クエリ
    # --------------------------------------------------------

    main_fields = model_answer.get(
        "fields",
        {}
    )

    for field, answer in main_fields.items():

        evaluation_items.append({
            "item": f"最終クエリ：{field}",
            "model_answer": answer,
            "location": "最終クエリ",
            "field": field
        })

    # --------------------------------------------------------
    # SQL全体が未回答
    # --------------------------------------------------------

    if not student_answer:

        results = []

        for item in evaluation_items:

            results.append({
                "item": item["item"],
                "answer": "",
                "grade": "×",
                "score": 0.0,
                "reason": "回答がないため。"
            })

        return {
            "sql": sql_name,
            "score": 0.0,
            "max_score": len(evaluation_items),
            "items": results
        }

    # --------------------------------------------------------
    # GPT採点
    # --------------------------------------------------------

    system_prompt = COMMON_RULES + """

【複合クエリの追加ルール】

SQL7やSQL8では、
サブクエリと最終クエリを区別して採点してください。


1. 必要なサブクエリそのものが存在しない場合、
   そのサブクエリの各評価項目は×とする。

2. 最終クエリの内容を、
   存在しないサブクエリの回答として
   流用してはならない。

3. サブクエリの内容を、
   最終クエリの回答として
   勝手に流用してはならない。

4. サブクエリが存在しており、
   その中で必要な内容の一部だけが正しい場合は△とする。

5. 必要なテーブルが3つあり、
   そのうち2つだけ正しく指定されているなど、
   明確に一部だけ正しい場合は△とする。

6. 必要な結合条件が2つあり、
   そのうち1つだけ正しい場合は△とする。

7. 必要な属性が複数あり、
   一部だけ正しい場合は△とする。

8. 学生が模範解答とは異なる方式で回答していても、
   クエリの構造と意味が完全に同等であることが
   明確な場合のみ○としてよい。

9. 単にキーワード、テーブル名、属性名などが
   学生答案のどこかに存在するだけでは
   ○や△にしてはならない。

10. 学生が実際にどの部分に何を書いているかを
    重視して判定すること。
    
    
11. サブクエリ側に必要な条件を、
    最終クエリ側にも必要であると誤って判断してはならない。
    サブクエリと最終クエリの役割を明確に区別すること。

12. 最終クエリの評価では、
    最終クエリに必要な内容だけを評価すること。

13. サブクエリが未作成であることによる減点は、
    原則としてサブクエリ側の評価項目で行う。
    同じ欠落を無関係な最終クエリの評価項目で
    二重に減点しないこと。


【出力形式】

必ず次のJSON形式だけを返してください。

{
  "items": [
    {
      "item": "指定された評価項目名",
      "grade": "○",
      "answer": "学生が実際に記述した内容",
      "reason": "簡潔な理由"
    }
  ]
}

gradeには必ず
「○」「△」「×」
のいずれか1つだけを指定してください。

itemの名称は変更しないでください。

answerには、
その評価項目について学生が実際に記述した内容だけを
記載してください。

対応する回答が存在しない場合は、
answerを空文字 "" にしてください。

学生が書いていない内容を推測して
answerに記載してはいけません。
"""

    user_prompt = f"""
採点対象：
{sql_name}

【教員の模範解答】

{json.dumps(
    model_answer,
    ensure_ascii=False,
    indent=2
)}

【評価項目】

{json.dumps(
    evaluation_items,
    ensure_ascii=False,
    indent=2
)}

【学生の回答】

{json.dumps(
    student_answer,
    ensure_ascii=False,
    indent=2
)}

各評価項目について、
学生がその項目に対応する内容を
実際に記述しているか確認した上で、
○、△、×で評価してください。

存在しないサブクエリを推測して
補完しないでください。
"""

    gpt_result = call_gpt_json(
        system_prompt,
        user_prompt
    )

    gpt_items = {}

    for item in gpt_result.get(
        "items",
        []
    ):

        item_name = item.get(
            "item",
            ""
        )

        if item_name:
            gpt_items[item_name] = item

    # --------------------------------------------------------
    # Python側で結果確定
    # --------------------------------------------------------

    results = []
    total_score = 0.0

    for evaluation_item in evaluation_items:

        item_name = evaluation_item[
            "item"
        ]

        gpt_item = gpt_items.get(
            item_name,
            {}
        )

        answer = gpt_item.get(
            "answer",
            ""
        )

        grade = normalize_grade(
            gpt_item.get(
                "grade",
                "×"
            )
        )

        reason = sanitize_reason(
            gpt_item.get(
                "reason",
                "判定結果を取得できなかったため。"
            )
        )

        # 回答そのものが存在しないなら必ず×
        if not str(answer).strip():

            grade = "×"

            if not reason.strip():
                reason = "対応する回答がないため。"

        score = SCORE_MAP[grade]

        total_score += score

        results.append({
            "item": item_name,
            "answer": answer,
            "grade": grade,
            "score": score,
            "reason": reason
        })

    return {
        "sql": sql_name,
        "score": total_score,
        "max_score": len(evaluation_items),
        "items": results
    }


# ============================================================
# 課題2 全体
# ============================================================

def grade_assignment2(
    student_assignment2
):

    model_answers = load_model_answers()

    results = {}

    total_score = 0.0
    total_max_score = 0

    # 模範解答側を基準にSQL1～SQL8を採点する
    # 学生がSQLを丸ごと未回答でも0点として扱う

    for sql_name, model_answer in model_answers.items():

        student_answer = student_assignment2.get(
            sql_name
        )

        if model_answer.get(
            "subqueries"
        ):

            result = grade_complex_query(
                sql_name,
                model_answer,
                student_answer
            )

        else:

            result = grade_standard_query(
                sql_name,
                model_answer,
                student_answer
            )

        results[sql_name] = result

        total_score += result[
            "score"
        ]

        total_max_score += result[
            "max_score"
        ]

    return {
        "queries": results,
        "total_score": total_score,
        "max_score": total_max_score
    }
    
# ============================================================
# 課題4 企画クエリ採点
# ============================================================

ER_SCHEMA_PATH = "data/er/er_schema_2026.json"
EXISTING_QUERIES_PATH = "data/model/week4_existing_queries_2026.json"


def load_er_schema():
    """2026年度のERスキーマを読み込む"""

    with open(
        ER_SCHEMA_PATH,
        "r",
        encoding="utf-8"
    ) as f:
        return json.load(f)


def load_existing_queries():
    """オリジナリティ比較用の既存クエリを読み込む"""

    with open(
        EXISTING_QUERIES_PATH,
        "r",
        encoding="utf-8"
    ) as f:
        return json.load(f)


def make_zero_project_result(
    project_name,
    project_answer
):
    """
    未回答の企画クエリはGPTに送らず、
    Python側で0点を確定する。
    """

    project_type = ""

    if project_answer:
        project_type = project_answer.get(
            "type",
            ""
        )

    return {
        "project": project_name,
        "type": project_type,
        "answered": False,

        "validity": {
            "score": 0,
            "reason": "企画意図およびクエリ設計が記述されていないため。"
        },

        "originality": {
            "score": 0,
            "reason": "企画内容が記述されていないため評価できない。"
        },

        "usefulness": {
            "score": 0,
            "reason": "企画内容が記述されていないため評価できない。"
        },

        "total_score": 0,
        "max_score": 15
    }


def normalize_project_score(value):
    """
    GPTが返した点数を0～5の整数に制限する。
    """

    try:
        score = int(value)
    except (TypeError, ValueError):
        return 0

    return max(
        0,
        min(5, score)
    )


def grade_project_query(
    project_name,
    project_answer,
    er_schema,
    existing_queries
):
    """
    企画クエリ1問を
    妥当性・オリジナリティ・有用性の
    3観点で採点する。
    """

    # --------------------------------------------------------
    # 未回答
    # --------------------------------------------------------

    if not project_answer:
        return make_zero_project_result(
            project_name,
            project_answer
        )

    answered = project_answer.get(
        "answered",
        False
    )

    if not answered:
        return make_zero_project_result(
            project_name,
            project_answer
        )

    # --------------------------------------------------------
    # 学生答案
    # --------------------------------------------------------

    project_type = project_answer.get(
        "type",
        ""
    )

    intent = project_answer.get(
        "intent",
        ""
    )

    design = project_answer.get(
        "design",
        {}
    )

    raw = project_answer.get(
        "raw",
        ""
    )

    # --------------------------------------------------------
    # GPT用プロンプト
    # --------------------------------------------------------

    system_prompt = """
あなたは大学の情報システム実験における
企画クエリ設計レポートの採点者です。

学生が自ら企画したクエリについて、

1. 妥当性
2. オリジナリティ
3. 有用性

の3つの観点から、
それぞれ0～5点で評価してください。

各観点について、
必ず点数と理由を出力してください。


============================================================
【妥当性】
============================================================

学生の企画意図とクエリ設計、および与えられたERスキーマを
照合して評価してください。

5点：
企画意図が明確であり、
ERスキーマ上で実現可能で、
クエリ設計が企画意図と十分に整合している。

4点：
基本的に妥当で実現可能であり、
企画意図と設計も概ね整合している。
ただし軽微な不足や曖昧さがある。

3点：
企画として成立しているが、
企画意図またはクエリ設計に
不明確な部分や改善すべき点がある。

2点：
企画意図は理解できるが、
ERスキーマとの対応やクエリ設計に
大きな問題がある。

1点：
企画意図または設計に重大な問題があり、
意図した結果を得ることが難しい。

0点：
企画として成立していない、
ERスキーマ上で実現できない、
または情報不足で評価できない。


【妥当性の重要ルール】

・ERスキーマに存在するテーブル、属性、関係を確認すること。

・存在しないテーブルや属性を、
  存在するものとして扱ってはならない。

・企画意図だけではなく、
  実際のクエリ設計との整合性も評価すること。

・クエリが複雑だから高得点にしてはならない。


============================================================
【オリジナリティ】
============================================================

学生の企画クエリを、
既存クエリと比較して評価してください。

5点：
目的、取得結果、処理内容が既存クエリと明確に異なり、
高いオリジナリティがある。

4点：
全体として独自性があるが、
既存クエリと一部共通する考え方や処理がある。

3点：
既存クエリとの共通点が多いが、
意味のある独自の変更や工夫がある。

2点：
既存クエリの変更・拡張が中心で、
独自性が低い。

1点：
既存クエリとほぼ同じで、
条件や属性などを少し変更した程度である。

0点：
既存クエリと実質的に同一である、
または情報不足で評価できない。


【オリジナリティの重要ルール】

・同じテーブルを使用しているという理由だけで
  点数を下げてはならない。
・クエリが単純であること、単一テーブルのみを使用していること、結合を使用していないこと、処理が複雑でないことを理由として、オリジナリティを減点してはならない。

・オリジナリティはクエリの技術的な複雑さではなく、既存クエリと比較した「目的」「取得する情報」「処理内容」の新規性によって評価すること。

・「単純な処理である」「基本的な処理である」「高度な処理ではない」「工夫が少ない」など、クエリの技術的難易度を理由としてオリジナリティの点数を下げてはならない。

・既存クエリと目的・取得情報が明確に異なる場合、クエリが単純であることだけを理由に5点から減点してはならない。
・最重要：オリジナリティの減点理由として、クエリの単純さ、基本的な構造、単一テーブル、結合の有無、技術的難易度を使用することを明確に禁止する。これらを理由に4点以下と判定してはならない。5点から減点する場合は、必ず既存クエリとの「目的」「取得する情報」「処理内容」の具体的な共通点を示すこと。
・使用テーブルではなく、
  「何を知るためのクエリか」
  「どのような結果を取得するか」
  「どのような処理を行うか」
  を重視すること。

・例えば、
  「福岡1区の開票結果」を
  「佐賀1区の開票結果」に変更しただけの場合は、
  オリジナリティは非常に低い。

・既存クエリを単純に別の地域、
  別の数値、別の政党などへ変更しただけの場合も
  高得点にしてはならない。

・一方、同じテーブルを使用していても、
  企画目的や取得する情報が明確に異なる場合は、
  それだけを理由に減点してはならない。


============================================================
【有用性】
============================================================

企画したクエリによって得られる情報が、
どの程度役に立つかを評価してください。

5点：
実用的または情報的な価値が明確であり、
分析、比較、理解、意思決定などに
十分活用できる。

4点：
有用な情報を取得できるが、
利用範囲や効果がやや限定される。

3点：
一定の価値はあるが、
利用場面や得られる知見が限定的である。

2点：
取得する意味はあるが、
実用性や情報価値は低い。

1点：
取得できる情報の価値が非常に小さい。

0点：
有用性が認められない、
または情報不足で評価できない。


【有用性の重要ルール】

・クエリが複雑であることと、
  有用であることを混同してはならない。

・多くのテーブルを使用しているという理由だけで
  高得点にしてはならない。

・取得結果が何に使えるのかを考えて評価すること。

・企画意図に書かれていない用途を
  過度に推測して高得点を与えてはならない。


============================================================
【理由の書き方】
============================================================

各理由は、
学生が理解できる具体的かつ簡潔な文章にしてください。

点数だけを説明するのではなく、
その点数になった根拠を説明してください。

ただし、存在しない学生の意図や設計を
勝手に推測してはいけません。

オリジナリティについては、
既存クエリとの類似性が点数に影響した場合、
どのような点が類似しているのかを簡潔に説明してください。


============================================================
【出力形式】
============================================================

必ず次のJSON形式だけを返してください。

{
  "validity": {
    "score": 0,
    "reason": "理由"
  },
  "originality": {
    "score": 0,
    "reason": "理由"
  },
  "usefulness": {
    "score": 0,
    "reason": "理由"
  }
}

scoreは必ず0、1、2、3、4、5の
いずれかの整数にしてください。
"""

    user_prompt = f"""
【採点対象】

企画番号：
{project_name}

企画種別：
{project_type}

企画意図：
{intent}


【学生のクエリ設計】

{json.dumps(
    design,
    ensure_ascii=False,
    indent=2
)}


【学生答案の原文】

{raw}


【2026年度 ERスキーマ】

{json.dumps(
    er_schema,
    ensure_ascii=False,
    indent=2
)}


【既存クエリ】

{json.dumps(
    existing_queries,
    ensure_ascii=False,
    indent=2
)}


以上を踏まえて、

・妥当性
・オリジナリティ
・有用性

をそれぞれ0～5点で評価し、
各観点について理由を記述してください。
"""

    gpt_result = call_gpt_json(
        system_prompt,
        user_prompt
    )

    # --------------------------------------------------------
    # Python側で点数を確定
    # --------------------------------------------------------

    validity_data = gpt_result.get(
        "validity",
        {}
    )

    originality_data = gpt_result.get(
        "originality",
        {}
    )

    usefulness_data = gpt_result.get(
        "usefulness",
        {}
    )

    validity_score = normalize_project_score(
        validity_data.get(
            "score",
            0
        )
    )

    originality_score = normalize_project_score(
        originality_data.get(
            "score",
            0
        )
    )

    usefulness_score = normalize_project_score(
        usefulness_data.get(
            "score",
            0
        )
    )

    validity_reason = validity_data.get(
        "reason",
        "評価理由を取得できませんでした。"
    )

    originality_reason = originality_data.get(
        "reason",
        "評価理由を取得できませんでした。"
    )

    usefulness_reason = usefulness_data.get(
        "reason",
        "評価理由を取得できませんでした。"
    )

    total_score = (
        validity_score
        + originality_score
        + usefulness_score
    )

    return {
        "project": project_name,
        "type": project_type,
        "answered": True,

        "validity": {
            "score": validity_score,
            "reason": validity_reason
        },

        "originality": {
            "score": originality_score,
            "reason": originality_reason
        },

        "usefulness": {
            "score": usefulness_score,
            "reason": usefulness_reason
        },

        "total_score": total_score,
        "max_score": 15
    }


# ============================================================
# 課題4 全体採点
# ============================================================

def grade_assignment4(
    student_assignment4
):

    er_schema = load_er_schema()

    existing_queries = load_existing_queries()

    results = {}

    total_score = 0

    # 必ず4-1～4-3を評価する
    project_names = [
        "4-1",
        "4-2",
        "4-3"
    ]

    for project_name in project_names:

        project_answer = student_assignment4.get(
            project_name
        )

        result = grade_project_query(
            project_name,
            project_answer,
            er_schema,
            existing_queries
        )

        results[project_name] = result

        total_score += result[
            "total_score"
        ]

    return {
        "projects": results,
        "total_score": total_score,
        "max_score": 45
    }
# ============================================================
# 第4週 統合採点
# 課題2 + 課題4
# ============================================================

def grade_week4(parsed_report):
    """
    第4週レポート全体を採点する。

    課題2：
        SQL1～SQL8

    課題4：
        4-1～4-3
    """

    assignment2_data = parsed_report.get(
        "assignment2",
        {}
    )

    assignment4_data = parsed_report.get(
        "assignment4",
        {}
    )

    # 課題2を採点
    assignment2_result = grade_assignment2(
        assignment2_data
    )

    # 課題4を採点
    assignment4_result = grade_assignment4(
        assignment4_data
    )

    # 各課題の得点
    assignment2_score = assignment2_result.get(
        "total_score",
        0
    )

    assignment2_max = assignment2_result.get(
        "max_score",
        0
    )

    assignment4_score = assignment4_result.get(
        "total_score",
        0
    )

    assignment4_max = assignment4_result.get(
        "max_score",
        45
    )

    # 第4週全体
    total_score = (
        assignment2_score
        + assignment4_score
    )

    max_score = (
        assignment2_max
        + assignment4_max
    )

    return {
        "assignment2": assignment2_result,
        "assignment4": assignment4_result,
        "total_score": total_score,
        "max_score": max_score
    }

