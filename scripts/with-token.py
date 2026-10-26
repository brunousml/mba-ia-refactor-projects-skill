"""Gera a variante "flags ligadas" de uma lista de chamadas: adiciona X-Admin-Token a todas.

Uso: python3 scripts/with-token.py <requests.json> <token> <saida.json>
"""
import json
import sys

entrada, token, saida = sys.argv[1:4]
with open(entrada) as f:
    chamadas = json.load(f)
for chamada in chamadas:
    chamada.setdefault("headers", {})["X-Admin-Token"] = token
with open(saida, "w") as f:
    json.dump(chamadas, f, ensure_ascii=False, indent=2)
