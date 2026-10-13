from utils.er_reader import read_er_schema

er_path = "data/er/er_schema.json"

er_schema = read_er_schema(er_path)

print(er_schema)