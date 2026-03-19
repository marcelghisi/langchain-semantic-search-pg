# LangChain Semantic Search + PGVector

CLI Python para ingestao de PDF, busca semantica e chat com contexto vetorial no PostgreSQL + `pgvector`.

## O que este projeto faz

- ingere PDF no banco vetorial;
- executa busca semantica (`search`);
- responde perguntas com contexto recuperado (`chat`);
- suporta provedores `openai` e `gemini` com `-m`.

## Estrutura

```text
.
├── docker-compose.yml
├── docker/postgres/init.sql
├── requirements.txt
├── .env.example
├── src/
│   ├── common.py
│   ├── ingest.py
│   ├── search.py
│   ├── chat.py
│   ├── delete.py
│   └── cli.py
├── document.pdf
└── README.md
```

## Quickstart (local)

1) Suba o banco:

```bash
docker context use default
docker compose up -d
```

2) Instale dependencias:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

3) Configure ambiente:

```bash
cp .env.example .env
python src/cli.py config
```

4) Ingestao (uma vez por documento):

```bash
python src/ingest.py --file document.pdf -m openai
```

5) Consulta e chat:

```bash
python src/search.py "resuma o documento" --k 10 -m openai
python src/chat.py --message "quais os pontos principais?" -m openai
```

## Uso direto dos scripts (recomendado)

Os scripts `ingest.py`, `search.py` e `chat.py` podem ser executados diretamente, sem passar pelo CLI.

### ingest.py

Ingere PDF no banco vetorial.

```bash
python src/ingest.py [--file ARQUIVO] [-m openai|gemini]
```

| Argumento | Descricao | Padrao |
|-----------|-----------|--------|
| `--file` | Caminho do PDF | `document.pdf` |
| `-m` | Provedor de embeddings | config padrao |

```bash
python src/ingest.py --file document.pdf -m openai
python src/ingest.py -m gemini
```

### search.py

Busca semantica no pgvector.

```bash
python src/search.py QUERY [--k N] [-m openai|gemini]
```

| Argumento | Descricao | Padrao |
|-----------|-----------|--------|
| `QUERY` | Texto da consulta (obrigatorio) | - |
| `--k` | Numero de resultados | 3 |
| `-m` | Provedor de embeddings | config padrao |

```bash
python src/search.py "resuma o documento" -m openai
python src/search.py "pontos principais" --k 10 -m gemini
```

### chat.py

Chat com contexto recuperado do banco vetorial.

```bash
python src/chat.py [--message PERGUNTA] [--k N] [-m openai|gemini]
```

| Argumento | Descricao | Padrao |
|-----------|-----------|--------|
| `--message` | Pergunta unica (se omitido, inicia chat interativo) | - |
| `--k` | Top K resultados do contexto | 3 |
| `-m` | Provedor do LLM | config padrao |

```bash
# Mensagem unica
python src/chat.py --message "quais os pontos principais?" -m openai

# Chat interativo (digite 'sair' para encerrar)
python src/chat.py -m openai

python src/chat.py --message "resuma em 3 pontos" --k 10 -m gemini
```

## Uso via CLI

Alternativamente, use o CLI unificado `cli.py` para todos os comandos:

```bash
python src/cli.py -h
```

Comandos disponiveis:

- `config`: salva configuracoes.
- `ingest --file ... -m ...`: ingere PDF.
- `list [-m ...] [--limit ...] [--offset ...] [--source-contains ...]`: lista documentos.
- `search "query" --k ... -m ...`: busca semantica.
- `chat [--message ...] --k ... -m ...`: chat.
- `delete --id ... -m ...` ou `delete --source ... -m ...`: exclui documentos.

### Exemplos do CLI

```bash
# Configuracao
python src/cli.py config

# Ingestao
python src/cli.py ingest --file document.pdf -m openai

# Listagem para descobrir IDs
python src/cli.py list -m openai
python src/cli.py list -m openai --source-contains "document.pdf"

# Busca
python src/cli.py search "resuma o documento" --k 10 -m openai

# Chat interativo
python src/cli.py chat -m openai

# Chat com mensagem unica
python src/cli.py chat --message "resuma em 3 pontos" -m openai

# Exclusao por ID
python src/cli.py delete --id 1 -m openai

# Exclusao por source (caminho original)
python src/cli.py delete --source "/caminho/absoluto/document.pdf" -m openai

# Exclusao por source relativo (sera normalizado para caminho absoluto)
python src/cli.py delete --source "document.pdf" -m openai
```

### Atalhos globais do CLI

- `-f/--file`: atalho para ingestao (nao executa chat)
- `-c/--chat`: atalho para chat com mensagem unica
- `-m/--model`: escolhe provedor (`openai` ou `gemini`)

```bash
# Ingestao
python src/cli.py -m openai -f document.pdf

# Chat
python src/cli.py -m gemini -c "resuma o documento"
```

## Docker context remoto (ex.: Linux Mint)

Se o Docker estiver em contexto remoto, o banco nao estara no `localhost` do seu mac por padrao.

```bash
docker context ls
docker context use casa
docker compose up -d
```

Se a app Python rodar localmente, crie tunel SSH:

```bash
ssh -N -L 5432:127.0.0.1:5432 mintdocker
```

Com tunel ativo, mantenha:
- `PG_HOST=localhost`
- `PG_PORT=5432`

## Sobre `-m` no delete

No `delete`, `-m` nao chama API de modelo. Ele apenas escolhe qual tabela vetorial sera afetada:

- `-m openai` -> tabela `documents_openai`
- `-m gemini` -> tabela `documents_gemini`

## Modelos padrao

- OpenAI:
  - Embedding: `text-embedding-3-small`
  - LLM: `gpt-5-nano`
- Gemini:
  - Embedding: `models/embedding-001`
  - LLM: `gemini-2.5-flash-lite`

## Credenciais padrao do banco (compose)

- `PG_HOST=localhost`
- `PG_PORT=5432`
- `PG_DATABASE=ghisi_rag`
- `PG_USER=ghisi`
- `PG_PASSWORD=ghisi`

## Troubleshooting rapido

- **`Connection refused` em `localhost:5432`**
  - confira `docker context ls`;
  - em contexto remoto, use tunel SSH ou rode a app na mesma maquina do banco.

- **`database "ghisi_db" does not exist`**
  - ajuste para `PG_DATABASE=ghisi_rag` no `.env` ou no `config`.

- **`vector type not found in the database`**
  - confirme extensao:
    `docker compose exec pgvector psql -U ghisi -d ghisi_rag -c "\dx"`.
  - deve aparecer `vector` na lista.

- **OpenAI 400 sobre `temperature` com `gpt-5-nano`**
  - esse modelo nao aceita `temperature=0.1` nesse endpoint;
  - use valor padrao (`1`) ou omita o parametro.
