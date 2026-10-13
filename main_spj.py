from utils.docx_reader import read_docx
from utils.markdown_writer import to_markdown
from utils.question_splitter import (
    split_by_spj_questions,
    split_answer_blocks,
    merge_questions_and_answers
)
import os


def main():
    # ベースディレクトリ
    base_dir = os.path.dirname(os.path.abspath(__file__))

    # 入力・出力フォルダ
    student_dir = os.path.join(base_dir, "data", "2025_student")
    markdown_dir = os.path.join(base_dir, "data", "2025_markdown")
    os.makedirs(markdown_dir, exist_ok=True)

    # A01 ～ A10 を対象にする
    student_files = [f"A{i:02d}.docx" for i in range(1, 11)]

    for student_file in student_files:
        input_path = os.path.join(student_dir, student_file)

        if not os.path.exists(input_path):
            print(f"{student_file} が見つかりません。スキップします。")
            continue

        print(f"処理中: {student_file}")

        # 1. Word → テキスト抽出
        text = read_docx(input_path)

        # 2. 設問抽出
        questions = split_by_spj_questions(text)

        # 3. 回答ブロック抽出
        answer_blocks = split_answer_blocks(text)

        # 4. 設問と回答を結合
        merged = merge_questions_and_answers(
            questions=questions,
            answer_blocks=answer_blocks
        )

        # 5. Markdown変換
        md = to_markdown(merged)

        # 6. 保存
        output_filename = student_file.replace(".docx", ".md")
        output_path = os.path.join(markdown_dir, output_filename)

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(md)

        print(f"保存完了: {output_path}")

    print("すべての変換処理が完了しました。")


if __name__ == "__main__":
    main()