from utils.docx_reader import read_docx
from utils.question_splitter_week4 import split_week4_report
from week4_grader import grade_assignment2


# ============================================================
# テスト対象
# ============================================================

DOCX_PATH = "data/student/week04-01.docx"


# ============================================================
# Word読み込み
# ============================================================

print("Wordファイルを読み込んでいます...")

text = read_docx(DOCX_PATH)


# ============================================================
# 第4週レポートを構造化
# ============================================================

print("学生答案を解析しています...")

report = split_week4_report(text)

student_assignment2 = report["assignment2"]


# ============================================================
# 課題2をGPTで採点
# ============================================================

print("GPTによる採点を開始します...")
print()

result = grade_assignment2(student_assignment2)


# ============================================================
# 結果表示
# ============================================================

print("=" * 70)
print("第4週 課題2 採点結果")
print("=" * 70)


for sql_name, sql_result in result["queries"].items():

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
    
        # 1.0 → 1、0.0 → 0 と表示
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


# ============================================================
# 合計
# ============================================================

print("=" * 70)

print(
    f"合計："
    f"{result['total_score']} / "
    f"{result['max_score']} 点"
)

print("=" * 70)