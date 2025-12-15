import json

with open("frieda.json", "rb") as f:
    frieda = json.load(f)

print(frieda)
print(type(frieda))
new_frieda = frieda
new_frieda['address']['home'] = ('Berlin', 'Germany')
print(new_frieda)
print(type(new_frieda))
new_frieda_json = json.dumps(new_frieda)
print(new_frieda_json)
print(type(new_frieda_json))
new_frieda_ser_deser = json.loads(new_frieda_json)
print(new_frieda_ser_deser)
print(type(new_frieda_ser_deser))
print(new_frieda_json == new_frieda_ser_deser)