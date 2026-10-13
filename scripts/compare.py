"""Compara a linha de base com a execução pós-refatoração.

Uso: python3 scripts/compare.py <before.json> <after.json> [--valores campo1,campo2,...]

Regras:
- erro de conexão (status None) em qualquer lado é divergência;
- o status HTTP precisa ser igual;
- a estrutura do corpo (chaves e tipos) precisa ser igual. int e float contam
  como "numero"; em listas, os tipos de todos os itens são unidos e None é
  compatível com qualquer tipo;
- com --valores, os campos listados (em qualquer nível do corpo) também precisam
  ter o mesmo valor. Use para mensagens e contagens estáveis;
- chamadas novas no "depois" são só aviso.
Saída != 0 se houver divergência.
"""
import json
import sys


def tipo(valor):
    if valor is None:
        return "null"
    if isinstance(valor, bool):
        return "bool"
    if isinstance(valor, (int, float)):
        return "numero"
    return type(valor).__name__


def formato(valor):
    if isinstance(valor, dict):
        return {k: formato(v) for k, v in sorted(valor.items())}
    if isinstance(valor, list):
        return {"__lista__": unir([formato(v) for v in valor])}
    return tipo(valor)


def unir(formatos):
    """Une os formatos dos itens de uma lista num só, ignorando null."""
    sem_null = [f for f in formatos if f != "null"]
    if not sem_null:
        return "null" if formatos else "vazia"
    if all(isinstance(f, dict) and "__lista__" not in f for f in sem_null):
        chaves = set().union(*sem_null)
        return {k: unir([f.get(k, "null") for f in sem_null]) for k in sorted(chaves)}
    distintos = sorted({json.dumps(f, sort_keys=True) for f in sem_null})
    return json.loads(distintos[0]) if len(distintos) == 1 else {"__misto__": distintos}


def compativel(a, b):
    if a == b or "null" in (a, b):
        return True
    if isinstance(a, dict) and isinstance(b, dict):
        if a.keys() != b.keys():
            return False
        return all(compativel(a[k], b[k]) for k in a)
    return False


def valores(corpo, campos, prefixo=""):
    achados = {}
    if isinstance(corpo, dict):
        for k, v in corpo.items():
            caminho = f"{prefixo}.{k}" if prefixo else k
            if k in campos and not isinstance(v, (dict, list)):
                achados[caminho] = v
            achados.update(valores(v, campos, caminho))
    elif isinstance(corpo, list):
        for i, v in enumerate(corpo):
            achados.update(valores(v, campos, f"{prefixo}[{i}]"))
    return achados


def carregar(caminho):
    with open(caminho, encoding="utf-8") as f:
        dados = json.load(f)
    por_id = {}
    for r in dados:
        if r["id"] in por_id:
            sys.exit(f"ID duplicado em {caminho}: {r['id']}")
        por_id[r["id"]] = r
    return por_id


def main():
    args = sys.argv[1:]
    campos = set()
    if "--valores" in args:
        i = args.index("--valores")
        campos = set(args[i + 1].split(","))
        del args[i : i + 2]
    antes, depois = carregar(args[0]), carregar(args[1])

    divergencias = 0
    for chave, a in antes.items():
        d = depois.get(chave)
        if d is None:
            print(f"[AUSENTE] {chave}")
            divergencias += 1
        elif a.get("status") is None or d.get("status") is None:
            print(f"[CONEXAO] {chave}: antes={a.get('erro_conexao')} depois={d.get('erro_conexao')}")
            divergencias += 1
        elif a["status"] != d["status"]:
            print(f"[STATUS] {chave}: {a['status']} -> {d['status']}")
            divergencias += 1
        elif not compativel(formato(a.get("corpo")), formato(d.get("corpo"))):
            print(f"[FORMATO] {chave}: estrutura do corpo mudou")
            divergencias += 1
        elif campos and valores(a.get("corpo"), campos) != valores(d.get("corpo"), campos):
            print(f"[VALOR] {chave}: {valores(a.get('corpo'), campos)} -> {valores(d.get('corpo'), campos)}")
            divergencias += 1
    for chave in sorted(depois.keys() - antes.keys()):
        print(f"[AVISO] chamada nova: {chave}")
    print(f"{len(antes)} chamadas comparadas, {divergencias} divergências")
    sys.exit(1 if divergencias else 0)


if __name__ == "__main__":
    main()
