import re
from typing import Dict, List


def split_by_agg_questions(text: str) -> Dict[str, str]:
    # 全角数字 → 半角
    z2h = str.maketrans("１２３４５", "12345")
    text = text.translate(z2h)

    # SQL4, SQL5 を検出
    header_pattern = re.compile(r"^(?:2-\d+\s*[:：]\s*)?SQL\s*([45])", re.MULTILINE)
    matches = list(header_pattern.finditer(text))

    questions = {}

    for i, m in enumerate(matches):
        q_num = m.group(1)
        start = m.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        block = text[start:end].strip()
        questions[f"Q{q_num}"] = block.splitlines()[0]

    return questions


def split_answer_blocks(text: str):
    """
    「使用テーブル」から始まる回答ブロックのみを抽出する
    """
    lines = [line.strip() for line in text.splitlines() if line.strip()]

    blocks = []
    current = None

    for line in lines:
        if line == "使用テーブル":
            if current:
                blocks.append("\n".join(current))
            current = ["使用テーブル"]
        else:
            if current is not None:
                current.append(line)

    if current:
        blocks.append("\n".join(current))

    return blocks


def merge_questions_and_answers(
    questions: Dict[str, str],
    answer_blocks: List[str]
) -> Dict[str, str]:
    merged = {}

    sorted_questions = sorted(
        questions.items(),
        key=lambda x: int(x[0][1:])
    )

    for i, (q_key, q_text) in enumerate(sorted_questions):
        if i < len(answer_blocks):
            answer = answer_blocks[i]
        else:
            answer = "（未記入）"

        merged[q_key] = q_text + "\n" + answer

    return merged