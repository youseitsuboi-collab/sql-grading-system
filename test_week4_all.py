from utils.docx_reader import read_docx
from utils.question_splitter_week4 import split_week4_report
from week4_grader import grade_week4


STUDENT_FILE = "data/student/week04-01.docx"


print("Wordファイルを読み込んでいます...")

text = read_docx(STUDENT_FILE)


print("第4週レポートを解析しています...")

parsed = split_week4_report(text)


print("課題2・課題4の採点を開始します...")

result = grade_week4(parsed)


# ============================================================
# 課題2
# ============================================================

assignment2 = result["assignment2"]

print()
print("=" * 70)
print("課題2 SQL1～SQL8 採点結果")
print("=" * 70)

for sql_name, sql_result in assignment2["queries"].items():

    print()
    print(
        f"【{sql_name}】 "
        f"{sql_result['score']} / "
        f"{sql_result['max_score']} 点"
    )

    print("-" * 70)

    for item in sql_result["items"]:

        mark = item["grade"]
        score = item["score"]

        if score == int(score):
            score_text = str(int(score))
        else:
            score_text = str(score)

        answer = item["answer"]

        if not str(answer).strip():
            answer = "（未回答）"

        print(
            f"{mark} {item['item']} "
            f"[{score_text}点]"
        )

        print(
            f"  回答：{answer}"
        )

        print(
            f"  理由：{item['reason']}"
        )

        print()


print(
    f"課題2 合計："
    f"{assignment2['total_score']} / "
    f"{assignment2['max_score']} 点"
)


# ============================================================
# 課題4
# ============================================================

assignment4 = result["assignment4"]

print()
print("=" * 70)
print("課題4 企画クエリ 採点結果")
print("=" * 70)

for project_name, project_result in assignment4["projects"].items():

    project_type = project_result.get(
        "type",
        ""
    )

    title = project_name

    if project_type:
        title += f" {project_type}"

    print()
    print(
        f"【{title}】 "
        f"{project_result['total_score']} / 15 点"
    )

    print("-" * 70)

    validity = project_result["validity"]

    print(
        f"妥当性："
        f"{validity['score']} / 5点"
    )

    print(
        f"  理由：{validity['reason']}"
    )

    print()

    originality = project_result["originality"]

    print(
        f"オリジナリティ："
        f"{originality['score']} / 5点"
    )

    print(
        f"  理由：{originality['reason']}"
    )

    print()

    usefulness = project_result["usefulness"]

    print(
        f"有用性："
        f"{usefulness['score']} / 5点"
    )

    print(
        f"  理由：{usefulness['reason']}"
    )

    print()


print(
    f"課題4 合計："
    f"{assignment4['total_score']} / "
    f"{assignment4['max_score']} 点"
)


# ============================================================
# 第4週全体
# ============================================================

print()
print("=" * 70)
print("第4週 採点結果")
print("=" * 70)

print(
    f"課題2："
    f"{assignment2['total_score']} / "
    f"{assignment2['max_score']} 点"
)

print(
    f"課題4："
    f"{assignment4['total_score']} / "
    f"{assignment4['max_score']} 点"
)

print("-" * 70)

print(
    f"合計："
    f"{result['total_score']} / "
    f"{result['max_score']} 点"
)

print("=" * 70)

