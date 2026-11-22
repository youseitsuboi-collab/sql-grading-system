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
    """複数項目が同一行にある形式・別名表記にも対応する。"""
    fields = {}
    current_field = None
    values = []

    aliases = {
        "グループ化": "行見出し",
        "選択条件 集計後": "選択条件（集計後）",
        "選択条件 集計前": "選択条件（集計前）",
    }
    names = sorted(set(ALL_FIELDS) | set(aliases), key=len, reverse=True)
    # ラベルの直後はコロン、または「並べ替え条件なし」の形式。
    label_re = re.compile(
        r"(?<![\w一-龥])(" + "|".join(map(re.escape, names)) +
        r")(?:[ \t]*[:：][ \t]*|[ \t]{2,}|(?=$))"
    )
    no_sort_re = re.compile(r"^並べ替え条件\s*なし$")
    unknown_heading_re = re.compile(
        r"^(?:クエリーの種類|設計方針|サブクエリーの条件|クエリー名)\s*[:：]"
    )

    def save():
        if current_field is not None:
            value = "\n".join(values).strip()
            if value:
                fields[current_field] = value

    for line in lines:
        line = line.strip()
        # Wordのセル結合で「なし選択条件」のようにラベルが連結される場合。
        line = re.sub(r"なし(?=(?:選択条件(?:（集計前）|（集計後）)?|結合条件|行見出し|列見出し|集計方法|射影属性|並べ替え条件)\s*[:：])", "なし ", line)
        if no_sort_re.fullmatch(line):
            save()
            current_field = "並べ替え条件"
            values = ["なし"]
            continue
        if unknown_heading_re.match(line):
            save()
            current_field = None
            values = []
            continue

        matches = list(label_re.finditer(line))
        if matches:
            save()
            for i, match in enumerate(matches):
                key = aliases.get(match.group(1), match.group(1))
                stop = matches[i + 1].start() if i + 1 < len(matches) else len(line)
                value = line[match.end():stop].strip()
                # 後続項目を同じフィールドに連結しない。
                if i == len(matches) - 1:
                    current_field = key
                    values = [value] if value else []
                elif value:
                    fields[key] = value
            continue

        if current_field is not None:
            values.append(line)
    save()
    return fields


def parse_query_block(block: str) -> Dict:
    """
    1つのクエリ設計を構造化する。
    未記入の項目も検出する。
    """

    lines = clean_lines(block)
    fields = extract_fields(lines)

    missing_fields = [
        field_name
        for field_name, value in fields.items()
        if not value.strip() or value.strip() == "【未記入】"
    ]

    return {
        "query_type": detect_query_type(lines),
        "query_name": extract_query_name(lines),
        "fields": fields,
        "missing_fields": missing_fields,
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
        r"^[^\S\n]*課題[^\S\n]*4(?=[^\S\n]*[:：]|[^\S\n]+[^\n]|[^\S\n]*$)",
        text,
        re.MULTILINE
    )

    if assignment4_match:
        target = text[:assignment4_match.start()]
    else:
        # 課題4の大見出しが省略され、4-1から始まる提出にも対応。
        # 課題2の範囲を4-1より前に限定する。
        first_project = re.search(
            r"(?m)^[ \t]*4[ \t]*[-－ー][ \t]*1[ \t]*[:：][ \t]*[^\n]+",
            text,
        )
        target = text[:first_project.start()] if first_project else text

    # 2-1 SQL1 / 2-1：SPJクエリー / 2-7a：SPJクエリー を認識。
    # 行頭だけを対象にし、本文中のSQL番号を誤認しない。
    pattern = re.compile(
        r"^[^\S\n]*(?:2[\s]*[-－ー][\s]*([1-8])([a-zA-Z]?)[^\S\n]*[:：]?[^\S\n]*(?:SQL[\s]*[1-8]\b|(?:SPJ|集計|不一致|入れ子|ユニオン|重複|SQL)[^\n]*?クエリ(?:ー)?|[^\n]*?クエリ(?:ー)?)|SQL[\s]*([1-8])\b)",
        re.MULTILINE | re.IGNORECASE,
    )
    matches = list(pattern.finditer(target))
    results = {}
    segments = {}
    for i, match in enumerate(matches):
        q_num = match.group(1) or match.group(3)
        end = matches[i + 1].start() if i + 1 < len(matches) else len(target)
        block = target[match.start():end].strip()
        segments.setdefault(f"SQL{q_num}", []).append(block)

    for key, blocks in segments.items():
        # SQL7/8は補助クエリーと最終クエリーをまとめて採点器に渡す。
        # 既存のgraderがrawを参照できるよう全ブロックを保持する。
        block = "\n".join(blocks)
        parsed = parse_query_block(block)
        parsed["raw"] = block
        results[key] = parsed

    return results


# ==================================================
# 課題4
# ==================================================

def extract_project_intent(block: str) -> str:
    """企画意図から、クエリー名・設計項目・SQL文の直前までを取得。"""
    match = re.search(r"^[ \t]*[・-]?[ \t]*企画意図[ \t]*[:：]?[ \t]*$", block, re.MULTILINE)
    if not match:
        return ""
    remainder = block[match.end():]
    end = re.search(
        r"^[ \t]*[・-]?[ \t]*(?:クエリー設計|クエリ設計|クエリー名[ \t]*[:：]|使用テーブル[ \t]*(?:[:：]|$)|SQL[ \t]*文[ \t]*$)",
        remainder, re.MULTILINE
    )
    return (remainder[:end.start()] if end else remainder).strip()


def extract_project_design(block: str) -> str:
    """クエリー設計の見出しがなくてもクエリー名以降を取得。"""
    match = re.search(
        r"^[ \t]*[・-]?[ \t]*(?:クエリー設計|クエリ設計|クエリー名[ \t]*[:：]|使用テーブル[ \t]*(?:[:：]|$))",
        block, re.MULTILINE
    )
    return block[match.start():].strip() if match else ""


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
        r"^[^\S\n]*課題[^\S\n]*4(?=[^\S\n]*[:：]|[^\S\n]+[^\n]|[^\S\n]*$)",
        text,
        re.MULTILINE
    )

    if assignment4_match:
        target = text[assignment4_match.start():]
    else:
        # 「課題4：企画クエリー」がない場合は、4-1～4-3の
        # 見出しが順番に現れることを確認してから4-1を開始点にする。
        headings = list(re.finditer(
            r"(?m)^[ \t]*4[ \t]*[-－ー][ \t]*([1-3])[ \t]*[:：][ \t]*[^\n]+",
            text,
        ))
        numbers = [m.group(1) for m in headings]
        if numbers[:3] != ["1", "2", "3"]:
            return {}
        target = text[headings[0].start():]

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
        # 末尾の記入用テンプレートを学生の回答に混ぜない。
        template = re.search(r"(?m)^[ \t]*クエリー設計テンプレート[ \t]*$", block)
        if template:
            block = block[:template.start()].rstrip()

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
            r"[^\S\n]*(?:[:：][^\S\n]*|[^\S\n]+)(.*)",
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
        if not answered and re.search(r"(?im)^\s*SELECT\s+\S+", block):
            answered = True

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
