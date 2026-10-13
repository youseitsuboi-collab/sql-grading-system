import re
from typing import Dict, List


# ==================================================
# 基本設定
# ==================================================

SPJ_FIELDS = [
    "使用テーブル",
    "結合条件",
    "選択条件",
    "射影属性",
    "並べ替え条件",
]

AGG_FIELDS = [
    "使用テーブル",
    "結合条件",
    "選択条件（集計前）",
    "行見出し",
    "列見出し",
    "集計方法",
    "選択条件（集計後）",
    "射影属性",
    "並べ替え条件",
]

ALL_FIELDS = sorted(
    set(SPJ_FIELDS + AGG_FIELDS),
    key=len,
    reverse=True
)


# ==================================================
# 共通処理
# ==================================================

def normalize_text(text: str) -> str:
    """
    Wordから読み込んだ文字列を解析しやすい形に整える。
    """

    z2h = str.maketrans(
        "０１２３４５６７８９",
        "0123456789"
    )

    text = text.translate(z2h)
    text = text.replace("\r\n", "\n")
    text = text.replace("\r", "\n")

    return text


def clean_lines(text: str) -> List[str]:
    """
    空行を除去し、前後の空白を取り除く。
    """

    return [
        line.strip()
        for line in text.splitlines()
        if line.strip()
    ]


# ==================================================
# クエリ設計解析
# ==================================================

def detect_query_type(lines: List[str]) -> str:
    """
    クエリ種類を判定する。
    """

    for line in lines:

        if line.startswith("SPJクエリー"):
            return "SPJ"

        if line.startswith("集計クエリー"):
            return "集計"

        if line.startswith("ユニオンクエリー"):
            return "ユニオン"

        if line.startswith("不一致クエリー"):
            return "不一致"

        if line.startswith("重複クエリー"):
            return "重複"

    return "不明"


def extract_query_name(lines: List[str]) -> str:
    """
    クエリ名を取得する。
    """

    prefixes = [
        "SPJクエリー",
        "集計クエリー",
        "ユニオンクエリー",
        "不一致クエリー",
        "重複クエリー",
    ]

    for line in lines:

        for prefix in prefixes:

            if line.startswith(prefix):

                parts = re.split(
                    r"[:：]",
                    line,
                    maxsplit=1
                )

                if len(parts) == 2:
                    return parts[1].strip()

    return ""


def extract_fields(lines: List[str]) -> Dict[str, str]:
    """
    使用テーブル、結合条件、選択条件などを抽出する。
    """

    fields = {}

    current_field = None
    current_values = []

    for line in lines:

        if line in ALL_FIELDS:

            if current_field is not None:

                fields[current_field] = "\n".join(
                    current_values
                ).strip()

            current_field = line
            current_values = []

        else:

            if current_field is not None:
                current_values.append(line)

    if current_field is not None:

        fields[current_field] = "\n".join(
            current_values
        ).strip()

    return fields


def parse_query_block(block: str) -> Dict:
    """
    1つのクエリ設計を構造化する。
    """

    lines = clean_lines(block)

    return {
        "query_type": detect_query_type(lines),
        "query_name": extract_query_name(lines),
        "fields": extract_fields(lines),
    }


# ==================================================
# 課題2
# ==================================================

def split_assignment2(text: str) -> Dict[str, Dict]:
    """
    課題2 SQL1～SQL8を抽出する。
    """

    text = normalize_text(text)

    # 課題4より前だけを対象にする
    assignment4_match = re.search(
        r"^\s*課題\s*4\s*[:：]",
        text,
        re.MULTILINE
    )

    if assignment4_match:
        target = text[:assignment4_match.start()]
    else:
        target = text

    pattern = re.compile(
        r"^\s*(?:2-\d+\s*[:：]?\s*)?"
        r"SQL\s*([1-8])\b",
        re.MULTILINE | re.IGNORECASE
    )

    matches = list(pattern.finditer(target))

    results = {}

    for i, match in enumerate(matches):

        q_num = match.group(1)

        start = match.start()

        if i + 1 < len(matches):
            end = matches[i + 1].start()
        else:
            end = len(target)

        block = target[start:end].strip()

        parsed = parse_query_block(block)

        # 元データも保持
        parsed["raw"] = block

        results[f"SQL{q_num}"] = parsed

    return results


# ==================================================
# 課題4
# ==================================================

def extract_project_intent(block: str) -> str:
    """
    企画意図を取得する。
    """

    match = re.search(
        r"企画意図\s*(.*?)\s*クエリー設計",
        block,
        re.DOTALL
    )

    if not match:
        return ""

    return match.group(1).strip()


def extract_project_design(block: str) -> str:
    """
    クエリー設計以降を取得する。
    """

    match = re.search(
        r"クエリー設計\s*(.*)",
        block,
        re.DOTALL
    )

    if not match:
        return ""

    return match.group(1).strip()


def is_real_query_name(query_name: str) -> bool:
    """
    学生が実際にクエリ名を入力しているか判定する。
    """

    name = query_name.strip()

    if not name:
        return False

    template_names = [
        "クエリー名を示すこと",
        "クエリ名を示すこと",
    ]

    if name in template_names:
        return False

    return True


def has_real_field_value(fields: Dict[str, str]) -> bool:
    """
    クエリ設計項目に学生が実際の値を入力しているか判定する。

    テンプレート説明文は回答として扱わない。
    """

    template_phrases = [
        "クエリー名を示すこと",
        "クエリ名を示すこと",
        "クエリーの種類",
        "ユニオンクエリー",
        "重複クエリー",
        "不一致クエリー",
        "元のテーブル/クエリー",
        "統合対象の組を生成するテーブル/クエリー",
        "テーブル/クエリー",
        "一致判定対象属性",
        "除外対象の組を生成するテーブル/クエリー",
        "一致判定条件",
        "ユニオンクエリーの中で使用するクエリーの設計は別途示すこと",
        "重複クエリーの中で使用するクエリーの設計は別途示すこと",
        "不一致クエリーの中で使用するクエリーの設計は別途示すこと",
    ]

    for value in fields.values():

        value = value.strip()

        if not value:
            continue

        # 複数行に分かれている場合にも対応
        lines = clean_lines(value)

        for line in lines:

            cleaned = line.strip()

            # 句読点の違いを吸収
            cleaned = cleaned.rstrip("。．")

            if not cleaned:
                continue

            # テンプレートそのものなら無視
            if cleaned in template_phrases:
                continue

            # 「○○クエリー：クエリー名を示すこと」
            # のようなテンプレートも無視
            if "クエリー名を示すこと" in cleaned:
                continue

            # テンプレート説明文
            if (
                "クエリーの設計は別途示すこと"
                in cleaned
            ):
                continue

            # ここまで残れば学生が書いた値とみなす
            return True

    return False


def is_answered_project(
    intent: str,
    design_text: str
) -> bool:
    """
    課題4が実際に回答されているか判定する。

    次のいずれかが存在すれば回答あり：
    ・企画意図
    ・実際のクエリ名
    ・実際の設計値

    Wordに元から存在するテンプレートだけの場合は
    未回答とする。
    """

    # 企画意図がある
    if intent.strip():
        return True

    parsed = parse_query_block(design_text)

    # 実際のクエリ名がある
    if is_real_query_name(
        parsed["query_name"]
    ):
        return True

    # 実際の設計値がある
    if has_real_field_value(
        parsed["fields"]
    ):
        return True

    return False


def split_assignment4(text: str) -> Dict[str, Dict]:
    """
    課題4 4-1～4-3を抽出する。
    """

    text = normalize_text(text)

    assignment4_match = re.search(
        r"^\s*課題\s*4\s*[:：]",
        text,
        re.MULTILINE
    )

    if not assignment4_match:
        return {}

    target = text[
        assignment4_match.start():
    ]

    pattern = re.compile(
        r"^\s*4\s*[-－ー]\s*([1-3])\b",
        re.MULTILINE
    )

    matches = list(
        pattern.finditer(target)
    )

    results = {}

    for i, match in enumerate(matches):

        q_num = match.group(1)

        start = match.start()

        if i + 1 < len(matches):
            end = matches[i + 1].start()
        else:
            end = len(target)

        block = target[
            start:end
        ].strip()

        lines = clean_lines(block)

        # ------------------------------------------
        # 4-1：結合質問
        # などから課題種類を取得
        # ------------------------------------------

        if lines:
            first_line = lines[0]
        else:
            first_line = ""

        type_match = re.match(
            r"4\s*[-－ー]\s*[1-3]"
            r"\s*[:：]\s*(.*)",
            first_line
        )

        if type_match:
            project_type = (
                type_match.group(1).strip()
            )
        else:
            project_type = ""

        # ------------------------------------------
        # 企画意図
        # ------------------------------------------

        intent = extract_project_intent(
            block
        )

        # ------------------------------------------
        # 設計部分
        # ------------------------------------------

        design_text = extract_project_design(
            block
        )

        # ------------------------------------------
        # 回答済みか判定
        # ------------------------------------------

        answered = is_answered_project(
            intent,
            design_text
        )

        # ------------------------------------------
        # 回答ありなら構造化
        # ------------------------------------------

        if answered:

            design = parse_query_block(
                design_text
            )

        else:

            design = {
                "query_type": "",
                "query_name": "",
                "fields": {}
            }

        # ------------------------------------------
        # 結果
        # ------------------------------------------

        results[f"4-{q_num}"] = {

            "type": project_type,

            "intent": intent,

            "answered": answered,

            "design": design,

            # 必要になった場合にGPTへ
            # 元文章を渡せるよう保持
            "raw": block
        }

    return results


# ==================================================
# 第4週全体
# ==================================================

def split_week4_report(text: str) -> Dict:
    """
    第4週レポート全体を解析する。

    課題2：
        SQL1～SQL8

    課題4：
        4-1～4-3
    """

    return {
        "assignment2":
            split_assignment2(text),

        "assignment4":
            split_assignment4(text)
    }