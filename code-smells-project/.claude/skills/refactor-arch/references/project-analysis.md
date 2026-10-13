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
3. **Router ou blueprint montado com prefixo:** combine o prefixo de montagem com o caminho interno. Sem combinar, o caminho fica errado.

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

## 6. Comando de boot e porta

- **Comando:** `scripts.start` (Node), bloco `if __name__ == "__main__"` ou `app.run(...)` (Python), README do projeto.
- **Porta:** procure em chamadas de `listen`, `run(port=...)`, variável `PORT` e no README.
- **Porta ocupada:** em macOS, a 5000 costuma estar em uso por um serviço do sistema. Teste antes de subir. Se estiver ocupada, use outra porta com o mesmo comando (flag de porta do servidor de desenvolvimento) e registre a escolha.
- **Ambiente isolado:** instale dependências num ambiente do próprio projeto (`.venv`, `node_modules`), nunca no ambiente global.

## 7. Contagem de arquivos

"Source files" conta apenas arquivos de código do projeto. Exclua `node_modules`, `.venv`, `venv`, `__pycache__`, `dist`, `build`, `.git` e lockfiles. Liste os caminhos de forma que a contagem possa ser conferida.
