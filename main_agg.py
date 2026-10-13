from utils.docx_reader import read_docx
from utils.markdown_writer import to_markdown
from utils.question_splitter_agg import (
    split_by_agg_questions,
    split_answer_blocks,
    merge_questions_and_answers
)
import os


def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))

    student_dir = os.path.join(base_dir, "data", "student", "student_agg")
    markdown_dir = os.path.join(base_dir, "data", "markdown", "agg")
    os.makedirs(markdown_dir, exist_ok=True)

    student_files = [f"G{i:02d}.docx" for i in range(1, 11)]

    for student_file in student_files:
        input_path = os.path.join(student_dir, student_file)

        if not os.path.exists(input_path):
            print(f"{student_file} が見つかりません。スキップします。")
            continue

        print(f"処理中: {student_file}")

        text = read_docx(input_path)
        questions = split_by_agg_questions(text)
        answer_blocks = split_answer_blocks(text)
        merged = merge_questions_and_answers(questions, answer_blocks)
        md = to_markdown(merged)

        output_filename = student_file.replace(".docx", ".md")
        output_path = os.path.join(markdown_dir, output_filename)

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(md)

        print(f"保存完了: {output_path}")

    print("集計クエリ用Markdown変換処理が完了しました。")


if __name__ == "__main__":
    main()