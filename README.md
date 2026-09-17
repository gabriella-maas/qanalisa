# QAnalisa

O **QAnalisa** é um assistente de Quality Assurance desenvolvido em **Python** para transformar tarefas do Jira em uma análise estruturada de testes.

A partir da chave de uma story, o QAnalisa coleta o **título** e a **descrição** no Jira, interpreta o requisito com apoio do **Claude Code**, cruza a alteração com uma base de conhecimento de ERP e gera contexto, regras de negócio, riscos, cenários de teste e sugestões de regressão.

```bash
qanalisa FN-1234
```

O objetivo é reduzir o trabalho repetitivo de copiar uma tarefa, contextualizá-la manualmente e reconstruir um plano de testes a cada nova demanda, sem substituir a análise crítica do QA.

---

## O que o QAnalisa faz

O fluxo principal é:

```text
                 Jira
                  │
          título + descrição
                  │
                  ▼
              QAnalisa
                  │
        ┌─────────┴─────────┐
        │                   │
 Base de conhecimento    Claude Code
      de ERP                 │
        │                   │
        └─────────┬─────────┘
                  ▼
          Análise estruturada
                  │
        ┌─────────┼─────────┐
        │         │         │
     Riscos    Cenários  Regressão
        │         │         │
        └─────────┴─────────┘
                  ▼
          Terminal + Markdown
```

Atualmente, a análise pode gerar:

- contextualização da tarefa;
- alterações identificadas;
- regras de negócio;
- pontos de atenção;
- impacto potencial entre módulos do ERP;
- cenários funcionais priorizados;
- cenários negativos e de borda;
- regressão sugerida;
- dúvidas ou lacunas do requisito;
- detalhamento de um cenário específico;
- bug report curto para comentário de Jira;
- bug report completo.

O QAnalisa diferencia informações extraídas do requisito de impactos inferidos, evitando tratar uma hipótese de regressão como uma regra confirmada do sistema.

---

## Exemplos de uso

### Analisar uma tarefa

```bash
qanalisa FN-1234
```

A análise também é armazenada localmente para evitar uma nova consulta e uma nova geração desnecessária.

### Forçar uma nova análise

```bash
qanalisa FN-1234 --reanalyze
```

### Detalhar um cenário

Depois que a tarefa já foi analisada:

```bash
qanalisa FN-1234 --test CT07
```

O QAnalisa utiliza a story e a análise já armazenadas para expandir o cenário com objetivo, pré-condições, passos, resultado esperado e riscos relacionados.

### Gerar um bug report curto

```bash
qanalisa bug FN-1234
```

A ferramenta solicita uma descrição livre do problema encontrado e utiliza o contexto da tarefa para gerar um texto conciso, adequado para comentário no Jira.

### Gerar um bug report completo

```bash
qanalisa bug FN-1234 --full
```

A versão completa contém:

- título;
- pré-condições;
- passos para reproduzir;
- resultado atual;
- resultado esperado;
- evidências;
- impacto.

---

## Workspace local

Cada tarefa analisada gera um workspace local em `.qa/`:

```text
.qa/
└── FN-1234/
    ├── story.json
    ├── analysis.json
    ├── analise-FN-1234.md
    └── bugs/
```

Esse diretório é local e **não deve ser versionado**, pois pode conter informações das tarefas analisadas.

---

## Tecnologias

O MVP utiliza:

- **Python 3.12+** — linguagem principal;
- **Typer** — interface de linha de comando;
- **Rich** — suporte à experiência no terminal;
- **HTTPX** — comunicação HTTP com o Jira Cloud;
- **Pydantic / Pydantic Settings** — modelos e configurações;
- **PyYAML** — base de conhecimento do ERP;
- **Claude Code** — análise de linguagem natural e geração estruturada;
- **Pytest** — testes automatizados.

O QAnalisa utiliza o Claude Code em modo não interativo e estruturado. A autenticação do Claude é mantida pelo próprio Claude Code; nenhuma credencial do Claude é armazenada pelo projeto.

---

## Arquitetura

O projeto foi dividido em componentes com responsabilidades específicas:

```text
src/qanalisa/
├── ai/             # integração com provedores de IA
├── analysis/       # análise, cenários, impacto e bugs
├── config/         # configurações de execução
├── jira/           # leitura e parsing de issues do Jira
├── knowledge/      # carregamento e matching da base de ERP
├── reports/        # geração de relatórios
├── storage/        # workspace e persistência local
├── cli.py          # comandos do terminal
└── models.py       # modelos estruturados

knowledge/
└── vrsuper/        # base de conhecimento utilizada pelo MVP

tests/              # testes automatizados
```

A integração com IA é isolada do restante da aplicação. Isso permite adicionar outros provedores futuramente sem reescrever o núcleo do QAnalisa.

---

## Requisitos

Antes de instalar, é necessário ter:

- Python **3.12 ou superior**;
- Git;
- acesso ao Jira Cloud que será consultado;
- token de API do Jira com as permissões necessárias de leitura;
- Claude Code instalado;
- Claude Code autenticado em uma conta autorizada.

Valide o Claude Code com:

```bash
claude --version
claude auth status
```

---

## Instalação

Clone o repositório:

```bash
git clone git@github.com:gabriella-maas/qanalisa.git
cd qanalisa
```

Crie e ative um ambiente virtual:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Instale o projeto e as dependências de desenvolvimento:

```bash
python -m pip install --upgrade pip
pip install -e ".[dev]"
```

Depois da instalação, o comando `qanalisa` fica disponível dentro do ambiente virtual.

---

## Configuração

Copie o arquivo de exemplo:

```bash
cp .env.example .env
```

Configure o `.env`:

```env
JIRA_BASE_URL=https://suaempresa.atlassian.net
JIRA_EMAIL=seu.email@empresa.com
JIRA_API_TOKEN=seu_token

AI_PROVIDER=claude_cli
CLAUDE_COMMAND=claude
CLAUDE_MODEL=
CLAUDE_TIMEOUT_SECONDS=120
```

> **Nunca versione o arquivo `.env`.**

O MVP acessa o Jira em modo de leitura. A geração do resultado acontece localmente e o QAnalisa não publica comentários automaticamente na tarefa.

---

## Claude Code

O QAnalisa executa o Claude Code de forma não interativa e espera uma resposta estruturada para continuar o pipeline.

A execução é isolada para reduzir interferências de configurações externas e não concede ferramentas ao modelo durante a análise.

Se a variável de ambiente `ANTHROPIC_API_KEY` estiver definida na máquina, o QAnalisa exibe um aviso, pois a configuração pode alterar a forma de autenticação/faturamento utilizada pelo Claude Code.

---

## Base de conhecimento de ERP

Além da descrição da story, o QAnalisa pode consultar uma base local com:

- módulos;
- funcionalidades;
- relacionamentos entre áreas;
- riscos conhecidos;
- fontes das relações;
- nível de confiança da informação.

Isso permite que a ferramenta sugira um regressivo considerando não apenas o texto explícito da tarefa, mas também os possíveis reflexos da alteração dentro de um ERP.

Exemplo conceitual:

```text
Alteração em Contas a Pagar
          │
          ▼
     Financeiro
      /      \
 Fiscal    Contábil
   │          │
   └──── possíveis pontos de regressão
```

Uma relação potencial não é apresentada como impacto confirmado: o objetivo é fornecer **pistas de investigação para o QA**.

> Em repositórios públicos, não devem ser versionadas regras internas, dados de clientes, stories reais ou conhecimentos confidenciais da organização. Bases privadas podem ser mantidas separadamente do código público.

---

## Testes

Execute a suíte automatizada com:

```bash
pytest -q
```

Os testes cobrem componentes como:

- parser do Jira;
- cliente do Jira;
- configurações;
- workspace local;
- matching da base de conhecimento;
- pipeline de análise;
- expansão de cenários;
- geração de bug reports;
- integração do CLI;
- provider do Claude Code.

As chamadas reais ao Claude são substituídas por doubles/mocks durante a suíte para não consumir a assinatura do usuário durante os testes automatizados.

---

## Segurança e privacidade

O QAnalisa foi desenhado para manter credenciais e dados operacionais fora do repositório.

Itens que **não devem ser commitados**:

```text
.env
.qa/
.qanalisa-private/
*.token
*.secret
credentials.*
```

Também não devem ser colocados em issues ou exemplos públicos:

- tokens de API;
- stories reais de projetos privados;
- screenshots internos;
- dados de clientes;
- respostas de sistemas internos;
- regras de negócio confidenciais.

---

## Roadmap

O MVP atual cobre análise de story, cenários e bug reports. Evoluções planejadas incluem:

- atualização assistida da base de conhecimento;
- comandos para visualizar e enriquecer conhecimento manual;
- suporte a múltiplas bases de ERP;
- análise de anexos da tarefa;
- análise de Pull Requests e diffs do GitHub;
- comparação entre requisito e implementação;
- histórico de regressões e riscos recorrentes;
- interface local opcional;
- suporte a outros provedores de IA.

---

## Status

**MVP em desenvolvimento ativo.**

O foco atual é validar o fluxo completo em tarefas reais, melhorar a qualidade dos cenários sugeridos e evoluir a base de conhecimento sem perder a distinção entre fato, documentação e inferência.

---

## Filosofia do projeto

O QAnalisa não pretende decidir o que deve ou não ser testado no lugar do QA.

Ele funciona como um **copiloto de análise**: organiza o requisito, amplia o campo de visão, aponta riscos e ajuda o profissional a chegar mais rápido a um plano de testes consistente.

> **QAnalisa — Entenda a story. Mapeie o risco. Teste melhor.**
