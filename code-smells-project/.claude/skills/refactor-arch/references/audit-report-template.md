# Template do relatório de auditoria (Fase 2)

O mesmo conteúdo vai para a saída e para o arquivo do relatório. Cada finding tem arquivo e linha exatos. Não existe "linha aproximada".

## Estrutura

Siga exatamente esta estrutura. Títulos de seção e de finding ficam em inglês, como no exemplo do formato. As descrições ficam no idioma da conversa.

````markdown
# Architecture Audit Report: <nome da pasta do projeto>

```
================================
ARCHITECTURE AUDIT REPORT
================================
Project: <nome da pasta do projeto>
Stack:   <linguagem> + <framework>
Files:   <N> analyzed | ~<M> lines of code
```

## Summary
CRITICAL: <n> | HIGH: <n> | MEDIUM: <n> | LOW: <n>

## Findings

### [CRITICAL] <Title in English> (AP-XX)
File: <arquivo>:<linha>[, <arquivo>:<inicio>-<fim>, ...]
Description: <o que está no código, em uma ou duas frases>
Impact: <o que pode acontecer, em uma frase>
Recommendation: <transformação do playbook, pelo ID (ex.: T02), e o que muda>

### [HIGH] ...

```
================================
Total: <N> findings
================================
```
````

## Regras

1. **Ordem:** CRITICAL, HIGH, MEDIUM, LOW. Dentro de cada severidade, ordene pelo primeiro `arquivo:linha` citado.
2. **Um finding por anti-pattern.** Se o mesmo anti-pattern aparece em várias linhas ou arquivos, faça um único finding e liste todos os `arquivo:linha` no campo `File:`. Exceção: se o mesmo anti-pattern tem severidades diferentes em lugares diferentes (por exemplo, AP-07 destrutivo e não destrutivo), faça um finding por severidade.
3. **Linhas exatas.** Antes de escrever, leia o trecho e confira o número. Intervalos seguem o formato `arquivo:inicio-fim`.
4. **Campos obrigatórios:** `File`, `Description`, `Impact` e `Recommendation`.
5. **APIs deprecated:** quando houver, o finding diz o símbolo obsoleto e o equivalente moderno.
6. **Total:** a soma dos findings precisa bater com o `Summary`.
7. **Sem findings inventados.** Se um anti-pattern não aparece, não o liste.

## Exemplo de finding

```markdown
### [CRITICAL] Plaintext Passwords (AP-04)
File: src/accounts/store.py:14, src/accounts/store.py:31-33
Description: A senha é gravada e comparada como texto puro, e a rota de detalhe da conta devolve o campo `password`.
Impact: Quem lê o banco ou a resposta da API obtém todas as senhas.
Recommendation: T04 (hash com salt) e T05 (serialização sem campos sensíveis). Exige refazer o seed.
```
