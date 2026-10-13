"""Compara a linha de base com a execução pós-refatoração.

Uso: python3 scripts/compare.py <before.json> <after.json>
Regras: o status HTTP precisa ser igual; o formato do corpo (estrutura de chaves
e tipos) precisa ser igual. Valores voláteis (datas, ids, timestamps) são ignorados.
Divergências são impressas; saída != 0 se houver alguma.
"""
import json
import sys


def formato(valor):
    if isinstance(valor, dict):
        return {k: formato(v) for k, v in sorted(valor.items())}
    if isinstance(valor, list):
        return [formato(valor[0])] if valor else []
    return type(valor).__name__


def main():
    with open(sys.argv[1], encoding="utf-8") as f:
        antes = {r["id"]: r for r in json.load(f)}
    with open(sys.argv[2], encoding="utf-8") as f:
        depois = {r["id"]: r for r in json.load(f)}

    divergencias = 0
    for chave, a in antes.items():
        d = depois.get(chave)
        if d is None:
            print(f"[AUSENTE] {chave}")
            divergencias += 1
            continue
        if a["status"] != d["status"]:
            print(f"[STATUS] {chave}: {a['status']} -> {d['status']}")
            divergencias += 1
        elif formato(a.get("corpo")) != formato(d.get("corpo")):
            print(f"[FORMATO] {chave}: estrutura do corpo mudou")
            divergencias += 1
    for chave in depois.keys() - antes.keys():
        print(f"[NOVA] {chave}")
    print(f"{len(antes)} chamadas comparadas, {divergencias} divergências")
    sys.exit(1 if divergencias else 0)


if __name__ == "__main__":
    main()
