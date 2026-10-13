from typing import Dict

def to_markdown(merged: Dict[str, str]) -> str:
    md = []

    for q_key, content in merged.items():
        lines = [line.strip() for line in content.splitlines() if line.strip()]

        question = lines[0]
        body = lines[1:]

        md.append(f"## {q_key}")
        md.append("**設問**")
        md.append(question)
        md.append("")
        md.append("**学生回答**")

        i = 0
        while i < len(body) - 1:
            key = body[i]
            value = body[i + 1]
            md.append(f"- {key}：{value}")
            i += 2

        md.append("")

    return "\n".join(md)
