# Template do relatório de auditoria (Fase 2)

O relatório é gravado no caminho recebido em `$ARGUMENTS`. Use a mesma estrutura na saída impressa e no arquivo. Cada finding tem arquivo e linha. Nada de "linha aproximada".

## Estrutura

```markdown
# Relatório de auditoria: <nome do projeto>

Project: <nome da pasta do projeto>
Stack:   <linguagem> + <framework>
Files:   <N> analyzed | ~<M> lines of code
Data:    <data da execução>

## Summary
CRITICAL: <n> | HIGH: <n> | MEDIUM: <n> | LOW: <n>

## Findings

### [CRITICAL] <título curto> (AP-XX)
File: <arquivo>:<linha> [, <arquivo>:<linha-linha>, ...]
Description: <o que está no código, em uma ou duas frases>
Impact: <o que pode acontecer, em uma frase>
Recommendation: <transformação do playbook, por ID, e o que muda>

### [HIGH] ...

## Total: <N> findings
```

## Regras

1. **Ordem:** CRITICAL, HIGH, MEDIUM, LOW. Dentro de cada severidade, ordene pela primeira linha citada.
2. **Um finding por anti-pattern e por arquivo.** Se o mesmo padrão aparece em várias linhas do mesmo arquivo, liste todas no campo `File:`. Se aparece em arquivos diferentes, um finding com vários `arquivo:linha`.
3. **Linhas exatas.** Antes de escrever, leia o trecho e confira o número. Intervalos seguem o formato `arquivo:inicio-fim`.
4. **Campos obrigatórios:** `File`, `Description`, `Impact` e `Recommendation` em todo finding.
5. **Total:** a soma dos findings precisa bater com o `Summary`.
6. **Sem findings inventados.** Se um anti-pattern não aparece, não o liste.
7. **Seções extras** (como "Anti-patterns remaining" ou comentários gerais) não entram no total.

## Exemplo de finding

```markdown
### [CRITICAL] Senha de conta armazenada em texto puro (AP-04)
File: src/users/store.py:14, src/users/store.py:31-33
Description: A senha é gravada e comparada como texto puro. A função de login também devolve o campo `password` na resposta.
Impact: Quem lê o banco ou a resposta da API tem todas as senhas.
Recommendation: T04 (hash com salt) e T05 (serialização sem campos sensíveis). Exige recriar o seed.
```
