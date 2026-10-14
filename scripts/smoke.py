"""Executa uma lista de chamadas HTTP e grava status + corpo de cada resposta.

Uso: python3 scripts/smoke.py <requests.json> <base_url> <saida.json>
Só usa a biblioteca padrão.
"""
import http.client
import json
import sys
import urllib.error
import urllib.request


def chamar(base_url, req):
    corpo = req.get("body")
    dados = json.dumps(corpo).encode() if corpo is not None else None
    cabecalhos = {"Content-Type": "application/json"} if dados is not None else {}
    cabecalhos.update(req.get("headers", {}))
    pedido = urllib.request.Request(
        base_url + req["path"], data=dados, method=req["method"], headers=cabecalhos
    )
    try:
        with urllib.request.urlopen(pedido, timeout=10) as resp:
            status, texto = resp.status, resp.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as erro:
        status, texto = erro.code, erro.read().decode("utf-8", "replace")
    except urllib.error.URLError as erro:
        return {"id": req["id"], "status": None, "erro_conexao": str(erro.reason)}
    except (TimeoutError, ConnectionError, http.client.HTTPException) as erro:
        return {"id": req["id"], "status": None, "erro_conexao": f"{type(erro).__name__}: {erro}"}
    try:
        corpo_resp = json.loads(texto)
    except ValueError:
        corpo_resp = texto
    return {"id": req["id"], "status": status, "corpo": corpo_resp}


def main():
    entrada, base_url, saida = sys.argv[1], sys.argv[2].rstrip("/"), sys.argv[3]
    with open(entrada, encoding="utf-8") as f:
        chamadas = json.load(f)
    resultados = [chamar(base_url, c) for c in chamadas]
    with open(saida, "w", encoding="utf-8") as f:
        json.dump(resultados, f, ensure_ascii=False, indent=2)
    print(f"{len(resultados)} chamadas gravadas em {saida}")


if __name__ == "__main__":
    main()
