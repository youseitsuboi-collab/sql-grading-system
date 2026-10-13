import re

def read_markdown(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def extract_q(text, q_num):
    pattern = rf"## Q{q_num}(.*?)(## Q{q_num+1}|$)"
    match = re.search(pattern, text, re.S)
    if match:
        return match.group(1).strip()
    return ""
