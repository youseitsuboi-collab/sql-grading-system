from utils.docx_reader import read_docx
from utils.question_splitter_week4 import split_week4_report
from week4_grader import grade_assignment4


STUDENT_FILE = "data/student/week04-01.docx"


print("Wordファイルを読み込んでいます...")

doc_data = read_docx(
    STUDENT_FILE
)


print("学生答案を解析しています...")

parsed = split_week4_report(
    doc_data
)


assignment4 = parsed[
    "assignment4"
]


print("GPTによる企画クエリ採点を開始します...")

result = grade_assignment4(
    assignment4
)


print()
print("=" * 70)
print("第4週 課題4 企画クエリ採点結果")
print("=" * 70)


for project_name, project_result in result["projects"].items():

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

    validity = project_result[
        "validity"
    ]

    print(
        f"妥当性：{validity['score']} / 5点"
    )

    print(
        f"  理由：{validity['reason']}"
    )

    print()

    originality = project_result[
        "originality"
    ]

    print(
        f"オリジナリティ："
        f"{originality['score']} / 5点"
    )

    print(
        f"  理由：{originality['reason']}"
    )

    print()

    usefulness = project_result[
        "usefulness"
    ]

    print(
        f"有用性：{usefulness['score']} / 5点"
    )

    print(
        f"  理由：{usefulness['reason']}"
    )

    print()


print("=" * 70)

print(
    f"課題4 合計："
    f"{result['total_score']} / "
    f"{result['max_score']} 点"
)

print("=" * 70)
