from pprint import pprint

from utils.docx_reader import read_docx
from utils.question_splitter_week4 import split_week4_report


DOCX_PATH = "data/student/week04-01.docx"

text = read_docx(DOCX_PATH)
result = split_week4_report(text)


print("\n" + "=" * 60)
print("課題2")
print("=" * 60)

for sql_name, data in result["assignment2"].items():

    print(f"\n【{sql_name}】")
    print(f"種類：{data['query_type']}")
    print(f"クエリ名：{data['query_name']}")

    for field, value in data["fields"].items():
        print(f"{field}：{value}")


print("\n" + "=" * 60)
print("課題4")
print("=" * 60)

for project_name, data in result["assignment4"].items():

    print(f"\n【{project_name}】")
    print(f"種類：{data['type']}")
    print(f"回答あり：{data['answered']}")
    print(f"企画意図：{data['intent']}")

    if data["answered"]:

        print(
            f"クエリ種類："
            f"{data['design']['query_type']}"
        )

        print(
            f"クエリ名："
            f"{data['design']['query_name']}"
        )

        print("設計内容：")

        pprint(
            data["design"]["fields"],
            sort_dicts=False
        )

    else:
        print("設計内容：（未回答）")