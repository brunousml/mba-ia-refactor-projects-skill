# Análise de projeto (Fase 1)

Objetivo: descobrir a stack, o banco, as rotas e a arquitetura atual sem supor nada. Cada conclusão precisa de um arquivo de evidência.

## 1. Manifestos: stack e versões

| Arquivo encontrado | Indica | Onde ler |
| --- | --- | --- |
| `requirements.txt`, `pyproject.toml`, `Pipfile`, `setup.py` | Python | Nome e versão de cada dependência: framework web, ORM, driver de banco, CORS |
| `package.json` | Node.js | `dependencies` (framework HTTP, driver de banco), `scripts.start` (comando de boot) |
| `package-lock.json`, `poetry.lock`, `uv.lock` | Versões travadas | Versão real instalada |
| `go.mod` | Go | `require` |
| `pom.xml`, `build.gradle` | Java/Kotlin | `dependencies` |
| `Gemfile` | Ruby | `gem` |
| `composer.json` | PHP | `require` |

Quando nenhum manifesto existir, use a extensão predominante dos arquivos de código e informe que a versão é desconhecida.

## 2. Imports: framework, banco e configuração

Procure nos arquivos de código (ignore dependências). O nome do pacote muda de stack para stack; o que se busca é o **papel**:

- **Framework HTTP:** pacote que oferece decorators de rota, chamadas de registro (`get`, `post`, `route`) ou um objeto de aplicação que escuta uma porta.
- **ORM ou mapeamento:** classes que herdam de uma base de modelo, ou declarações de coluna e relação.
- **Driver de banco:** conexão aberta a partir de um caminho de arquivo, URL (`postgres://`, `mysql://`) ou `:memory:`.
- **Configuração:** leitura de variáveis de ambiente (`os.environ`, `os.getenv`, `process.env`) ou de arquivo de config.
- **Segurança:** biblioteca de hash, tokens, CORS, autenticação.
- **Testes:** diretórios `tests/`, `spec/`, `__tests__/`.

## 3. Inventário de rotas

Registro de rota aparece de três formas. Procure as três:

1. **Decorator sobre função:** `@<objeto>.<método>("/caminho")`, `@route(...)`.
2. **Registro explícito:** `<objeto>.<método>("/caminho", handler)` ou chamada de adição de regra de URL.
3. **Módulo de rotas montado com prefixo** (router, grupo de rotas): combine o prefixo de montagem com o caminho interno. Sem essa combinação, o caminho fica errado.

Para cada rota, registre: método HTTP, caminho completo, `arquivo:linha` do registro e nome do handler. Inclua as rotas de administração, de exclusão e de relatório, que costumam ficar em arquivos secundários ou no próprio arquivo de entrada.

Se o mesmo caminho aparecer com métodos diferentes, cada combinação é uma rota.

## 4. Banco, tabelas e dados de seed

- **Schema:** procure `CREATE TABLE`, arquivos de migração e definições de modelo. Liste as tabelas ou entidades.
- **Banco volátil:** se a conexão for em memória, marque "volátil: dados recriados no boot" e localize o seed.
- **Seed:** arquivo ou função que insere dados iniciais. Anote onde está, porque ele precisa ser refeito quando o hash de senha muda.

## 5. Classificação da arquitetura

| Classificação | Sinais |
| --- | --- |
| **Monolito** | Poucos arquivos com roteamento, acesso a dados e regra de negócio misturados. Um arquivo passando de 300 linhas com mais de uma responsabilidade é sinal forte. |
| **Camadas parciais** | Existem diretórios separados (models, routes, services), mas a regra de negócio ainda está dentro das rotas ou o acesso a dados aparece fora da camada de dados. |
| **MVC** | Camadas separadas com controller. O entry point só compõe a aplicação. |

Diga qual classificação se aplica e por quê, com pelo menos dois arquivos de evidência.

## 6. Comando de boot e porta (usados só na Fase 3)

As Fases 1 e 2 são **só leitura**. Nelas você apenas identifica o comando e a porta. Não suba a aplicação, não instale dependências, não rode seed.

- **Comando:** `scripts.start` (Node), o bloco `if __name__ == "__main__"` ou a chamada `run(...)` (Python), ou o README do projeto. Se o bloco de entrada faz inicialização ou seed, o boot precisa passar por ele. Um servidor de desenvolvimento alternativo que pula esse bloco serve apenas quando a inicialização acontece em outro lugar.
- **Porta:** procure em `listen`, `run(port=...)`, variável `PORT` e no README.
- **Seed e estado:** banco em arquivo guarda o estado entre execuções. Localize o arquivo de banco e o seed, porque a Fase 3 precisa do mesmo estado inicial no snapshot e na validação.

Na Fase 3, antes do snapshot:
1. Instale as dependências num ambiente do próprio projeto (`.venv`, `node_modules`), nunca no global.
2. Verifique se a porta está livre (`lsof -iTCP:<porta> -sTCP:LISTEN`). No macOS, a 5000 costuma estar ocupada por um serviço do sistema, que responde 403 a tudo.
3. Se a porta estiver ocupada e for fixa no código, a primeira edição da Fase 3 é torná-la configurável por variável de ambiente, mantendo o mesmo default. Suba numa porta livre.
4. Depois de subir, confirme que a resposta vem da aplicação: uma rota raiz ou de health deve devolver o corpo esperado, não um erro genérico de outro serviço.

## 7. Contagem de arquivos

"Source files" conta apenas arquivos de código do projeto. Exclua `node_modules`, `.venv`, `venv`, `__pycache__`, `dist`, `build`, `.git` e lockfiles. Liste os caminhos de forma que a contagem possa ser conferida.
