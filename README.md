# LangChain Semantic Search + PGVector

Python CLI for PDF ingestion, semantic search, and chat with vector context on PostgreSQL + `pgvector`.

## What this project does

- ingests PDF into the vector database;
- runs semantic search (`search`);
- answers questions with retrieved context (`chat`);
- supports `openai` and `gemini` providers via `-m`.

## Structure

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

1) Start the database:

```bash
docker context use default
docker compose up -d
```

2) Install dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

3) Configure environment:

```bash
cp .env.example .env
python src/cli.py config
```

4) Ingest (once per document):

```bash
python src/ingest.py --file document.pdf -m openai
```

5) Search and chat:

```bash
python src/search.py "summarize the document" --k 10 -m openai
python src/chat.py --message "what are the main points?" -m openai
```

## Direct script usage (recommended)

The scripts `ingest.py`, `search.py`, and `chat.py` can be run directly without going through the CLI.

### ingest.py

Ingests PDF into the vector database.

```bash
python src/ingest.py [--file FILE] [-m openai|gemini]
```

| Argument | Description | Default |
|----------|-------------|---------|
| `--file` | Path to PDF | `document.pdf` |
| `-m` | Embedding provider | config default |

```bash
python src/ingest.py --file document.pdf -m openai
python src/ingest.py -m gemini
```

### search.py

Semantic search in pgvector.

```bash
python src/search.py QUERY [--k N] [-m openai|gemini]
```

| Argument | Description | Default |
|----------|-------------|---------|
| `QUERY` | Search text (required) | - |
| `--k` | Number of results | 3 |
| `-m` | Embedding provider | config default |

```bash
python src/search.py "summarize the document" -m openai
python src/search.py "main points" --k 10 -m gemini
```

### chat.py

Chat with context retrieved from the vector database.

```bash
python src/chat.py [--message QUESTION] [--k N] [-m openai|gemini]
```

| Argument | Description | Default |
|----------|-------------|---------|
| `--message` | Single question (if omitted, starts interactive chat) | - |
| `--k` | Top K results for context | 3 |
| `-m` | LLM provider | config default |

```bash
# Single message
python src/chat.py --message "what are the main points?" -m openai

# Interactive chat (type 'exit' to quit)
python src/chat.py -m openai

python src/chat.py --message "summarize in 3 points" --k 10 -m gemini
```

## CLI usage

Alternatively, use the unified CLI `cli.py` for all commands:

```bash
python src/cli.py -h
```

Available commands:

- `config`: saves configuration.
- `ingest --file ... -m ...`: ingests PDF.
- `list [-m ...] [--limit ...] [--offset ...] [--source-contains ...]`: lists documents.
- `search "query" --k ... -m ...`: semantic search.
- `chat [--message ...] --k ... -m ...`: chat.
- `delete --id ... -m ...` or `delete --source ... -m ...`: deletes documents.

### CLI examples

```bash
# Configuration
python src/cli.py config

# Ingest
python src/cli.py ingest --file document.pdf -m openai

# List to discover IDs
python src/cli.py list -m openai
python src/cli.py list -m openai --source-contains "document.pdf"

# Search
python src/cli.py search "summarize the document" --k 10 -m openai

# Interactive chat
python src/cli.py chat -m openai

# Single message chat
python src/cli.py chat --message "summarize in 3 points" -m openai

# Delete by ID
python src/cli.py delete --id 1 -m openai

# Delete by source (original path)
python src/cli.py delete --source "/absolute/path/document.pdf" -m openai

# Delete by relative source (will be normalized to absolute path)
python src/cli.py delete --source "document.pdf" -m openai
```

### CLI global shortcuts

- `-f/--file`: shortcut for ingest (does not run chat)
- `-c/--chat`: shortcut for single-message chat
- `-m/--model`: selects provider (`openai` or `gemini`)

```bash
# Ingest
python src/cli.py -m openai -f document.pdf

# Chat
python src/cli.py -m gemini -c "summarize the document"
```

## Remote Docker context (e.g. Linux Mint)

If Docker is in a remote context, the database will not be on your Mac's `localhost` by default.

```bash
docker context ls
docker context use casa
docker compose up -d
```

If the Python app runs locally, create an SSH tunnel:

```bash
ssh -N -L 5432:127.0.0.1:5432 mintdocker
```

With the tunnel active, keep:
- `PG_HOST=localhost`
- `PG_PORT=5432`

## About `-m` in delete

In `delete`, `-m` does not call a model API. It only selects which vector table is affected:

- `-m openai` -> table `documents_openai`
- `-m gemini` -> table `documents_gemini`

## Default models

- OpenAI:
  - Embedding: `text-embedding-3-small`
  - LLM: `gpt-5-nano`
- Gemini:
  - Embedding: `gemini-embedding-001` (or `models/embedding-001` if using older config)
  - LLM: `gemini-2.5-flash-lite`

## Default database credentials (compose)

- `PG_HOST=localhost`
- `PG_PORT=5432`
- `PG_DATABASE=ghisi_rag`
- `PG_USER=ghisi`
- `PG_PASSWORD=ghisi`

## Quick troubleshooting

- **`Connection refused` on `localhost:5432`**
  - check `docker context ls`;
  - with remote context, use SSH tunnel or run the app on the same machine as the database.

- **`database "ghisi_db" does not exist`**
  - set `PG_DATABASE=ghisi_rag` in `.env` or config.

- **`vector type not found in the database`**
  - confirm extension:
    `docker compose exec pgvector psql -U ghisi -d ghisi_rag -c "\dx"`.
  - `vector` should appear in the list.

- **OpenAI 400 on `temperature` with `gpt-5-nano`**
  - this model does not accept `temperature=0.1` on this endpoint;
  - use default value (`1`) or omit the parameter.
