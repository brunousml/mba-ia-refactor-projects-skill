# Guidelines da arquitetura MVC alvo (Fase 3)

O alvo é uma aplicação em que cada camada tem uma responsabilidade e depende só da camada abaixo dela. Os nomes de diretório abaixo são o padrão. Se o projeto já usa outro nome consistente (por exemplo `services/` no lugar de `models/` para acesso a dados), mantenha o nome dele e siga o mesmo princípio.

## Camadas

```
config/        configuração lida do ambiente, validada no boot
models/        acesso a dados: consultas, entidades, schema
services/      regra de negócio: cálculos, decisões, orquestração
controllers/   adaptação: lê a requisição, chama o serviço, monta a resposta
routes/        mapeamento: método + caminho -> controller (é a "view" da API)
middlewares/   transversal: autenticação, erro central, log de requisição
serializers/   (opcional) o que sai na resposta; esconde campos sensíveis
<entry point>  compõe a aplicação: carrega config, cria o app, registra middlewares e rotas, sobe o servidor
```

## Responsabilidades

| Camada | Pode | Não pode |
| --- | --- | --- |
| `config/` | Ler variáveis de ambiente, definir defaults de desenvolvimento, validar obrigatórios | Conter segredo literal; ter lógica de negócio |
| `models/` | Montar consultas com parâmetros, mapear linhas para entidades | Conhecer requisição ou resposta HTTP; formatar JSON; decidir regra de negócio |
| `services/` | Aplicar regra de negócio, chamar `models/`, lançar erros de domínio | Ler `request`, devolver `response`, conhecer status HTTP |
| `controllers/` | Validar formato da entrada, chamar serviços, escolher status | Consultar banco diretamente; calcular regra de domínio |
| `routes/` | Registrar método e caminho, aplicar middlewares da rota | Ter qualquer lógica além de apontar para o controller |
| `middlewares/` | Autenticar, tratar erro, registrar requisição | Regra de negócio |
| `serializers/` | Escolher os campos públicos de cada entidade | Consultar banco |
| Entry point | Compor: criar dependências e injetá-las | Regra, consulta ou rota definida inline |

## Regras de projeto

1. **Config por ambiente.** Segredos e endereços saem do código. Em desenvolvimento, um segredo ausente vira um valor aleatório com warning. Em produção, a ausência derruba o boot (T01). A porta padrão é **a mesma do projeto original**. O modo debug vem do ambiente, com default desligado. Inclua um `.env.example`.
2. **Injeção de dependência simples.** Banco, cache e serviços são criados no entry point e passados para quem usa. Nenhum módulo cria conexão por conta própria.
3. **Erros de domínio são classes.** O serviço lança um erro de domínio com status sugerido. O middleware de erro traduz para a resposta. Erro não tratado vira 500 com mensagem genérica e log completo no servidor.
4. **Serialização explícita.** A resposta é montada por um serializador que lista os campos públicos. Nunca se devolve a entidade inteira.
5. **Rotas perigosas ficam registradas, mas protegidas.** Operações destrutivas ou administrativas ficam atrás de uma flag de configuração (desabilitada por default, responde 403) e de autenticação quando ela existir. Documente a decisão no README.
6. **Contrato preservado.** Caminhos, métodos, códigos de status e nomes de campos da resposta não mudam, salvo as correções de segurança listadas na Fase 3.
7. **Nomes externos x internos.** Se a API recebe campos com nomes abreviados, mantenha esses nomes na borda (controller ou serializer) e use nomes descritivos dentro das camadas.

## Adaptação ao ponto de partida

**Monolito (um ou poucos arquivos com tudo):** divida por domínio. Para cada grupo de rotas relacionadas, crie controller, serviço e acesso a dados, e mova o código para a camada certa sem alterar a lógica. Só depois de tudo estar no lugar, aplique as correções de anti-pattern.

**Camadas parciais (já existem routes, models, services):** não reescreva o que já está correto. Procure o que falta: regra dentro de rota (mover para serviço), serialização sem filtro (criar serializador), configuração espalhada (centralizar), erro sem handler central (adicionar middleware). Preserve os nomes de módulo que já existem.

**Em qualquer caso:** prefira mover e renomear pequenos blocos a reescrever arquivos inteiros. Depois de cada movimento, rode o boot, para que um erro de import apareça cedo.

**Ordem:** a mesma da seção "Ordem de aplicação" do playbook. Primeiro a estrutura sem mudar lógica, depois segurança, depois regra e erros, por fim desempenho e limpeza.

## Estrutura mínima de um arquivo de rota

Exemplo genérico, em pseudocódigo comum às stacks:

```
# routes/itens.py
registrar("GET",    "/itens",      itens_controller.listar)
registrar("GET",    "/itens/{id}", itens_controller.buscar)
registrar("POST",   "/itens",      itens_controller.criar)
```

O arquivo só registra. Qualquer `if` ou consulta nele é sinal de que a lógica precisa ir para o controller ou o serviço.

## Checklist da estrutura final

- [ ] Existe um entry point que só compõe a aplicação
- [ ] Nenhum segredo literal no código (busca por AP-01 volta vazia)
- [ ] Toda consulta está em `models/` ou na camada de dados equivalente
- [ ] Rotas só fazem roteamento
- [ ] Controllers concentram o fluxo da aplicação (entrada → serviço → resposta), sem regra de domínio nem SQL
- [ ] Erros são tratados por um handler central
- [ ] Nenhuma entidade é devolvida inteira na resposta
- [ ] Rotas destrutivas ou administrativas estão protegidas
