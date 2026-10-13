import json

def read_er_schema(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)