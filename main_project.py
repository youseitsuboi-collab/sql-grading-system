from utils.docx_reader import read_docx
import os
import re


def format_project_markdown(student_id: str, text: str) -> str:
    # 不要なヘッダーっぽい部分を軽く除去
    remove_words = [
        "情報システム実験",
        "設計課題　レポート用紙",
        "学籍番号",
        "名  前",
        "課題",
        "第4回演習課題のクエリー設計および企画クエリーの企画意図を記述せよ。"
    ]

    lines = [line.strip() for line in text.splitlines() if line.strip()]
    lines = [line for line in lines if line not in remove_words and not re.match(r"^\d{4}年", line)]

    md = [f"# {student_id} 企画クエリ課題", ""]

    heading_map = {
        "4-1：結合質問": "## 4-1 結合質問",
        "4-2：集計質問": "## 4-2 集計質問",
        "4-3：入れ子質問（またはユニオンクエリー）": "## 4-3 入れ子質問（またはユニオンクエリー）",
        "企画意図": "### 企画意図",
        "クエリー設計": "### クエリー設計",
        "使用テーブル": "### 使用テーブル",
        "結合条件": "### 結合条件",
        "選択条件": "### 選択条件",
        "選択条件（集計前）": "### 選択条件（集計前）",
        "行見出し": "### 行見出し",
        "列見出し": "### 列見出し",
        "集計方法": "### 集計方法",
        "選択条件（集計後）": "### 選択条件（集計後）",
        "射影属性": "### 射影属性",
        "並べ替え条件": "### 並べ替え条件"
    }

    for line in lines:
        if line in heading_map:
            md.append("")
            md.append(heading_map[line])
        elif line.startswith("SPJクエリー") or line.startswith("集計クエリー"):
            md.append("")
            md.append(f"**{line}**")
        else:
            md.append(line)

    return "\n".join(md)


def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))

    student_dir = os.path.join(base_dir, "data", "student_project")
    markdown_dir = os.path.join(base_dir, "data", "markdown")
    os.makedirs(markdown_dir, exist_ok=True)

    student_files = [f"F{i:02d}.docx" for i in range(1, 11)]

    for student_file in student_files:
        input_path = os.path.join(student_dir, student_file)

        if not os.path.exists(input_path):
            print(f"{student_file} が見つかりません。スキップします。")
            continue

        print(f"変換中: {student_file}")

        text = read_docx(input_path)
        student_id = student_file.replace(".docx", "")

        md = format_project_markdown(student_id, text)

        output_path = os.path.join(markdown_dir, f"{student_id}.md")

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(md)

        print(f"保存完了: {output_path}")

    print("企画クエリのMarkdown変換が完了しました。")


if __name__ == "__main__":
    main()