from __future__ import annotations

import argparse

from common import configure_interactive


def main() -> int:
    parser = argparse.ArgumentParser(prog="ghisi", description="CLI principal do projeto.")
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("config", help="Solicita e salva configuracoes.")

    ingest_parser = subparsers.add_parser("ingest", help="Ingestao de PDF.")
    ingest_parser.add_argument(
        "--file", default="document.pdf", help="Caminho do arquivo PDF."
    )
    ingest_parser.add_argument(
        "-m",
        "--model",
        choices=["openai", "gemini"],
        help="Provedor de embeddings para ingestao.",
    )

    search_parser = subparsers.add_parser("search", help="Busca semantica.")
    search_parser.add_argument("query", help="Texto da consulta.")
    search_parser.add_argument("--k", type=int, default=3, help="Numero de resultados.")
    search_parser.add_argument(
        "-m",
        "--model",
        choices=["openai", "gemini"],
        help="Provedor de embeddings para busca.",
    )

    chat_parser = subparsers.add_parser("chat", help="Chat com contexto vetorial.")
    chat_parser.add_argument("--message", help="Pergunta unica.")
    chat_parser.add_argument("--k", type=int, default=3, help="Top K de contexto.")
    chat_parser.add_argument(
        "-m",
        "--model",
        choices=["openai", "gemini"],
        help="Provedor de LLM para responder.",
    )

    list_parser = subparsers.add_parser(
        "list", help="Lista documentos ingeridos no banco vetorial."
    )
    list_parser.add_argument(
        "-m",
        "--model",
        choices=["openai", "gemini"],
        help="Provedor da tabela vetorial.",
    )
    list_parser.add_argument("--limit", type=int, default=20, help="Quantidade maxima de itens.")
    list_parser.add_argument("--offset", type=int, default=0, help="Quantidade de itens para pular.")
    list_parser.add_argument(
        "--source-contains",
        help="Filtra por parte do caminho source.",
    )

    delete_parser = subparsers.add_parser(
        "delete", help="Remove documentos ingeridos do banco vetorial."
    )
    delete_parser.add_argument("--id", help="ID (UUID) do documento para remover.")
    delete_parser.add_argument(
        "--source",
        help="Caminho original (source) para remover todos os registros relacionados.",
    )
    delete_parser.add_argument(
        "-m",
        "--model",
        choices=["openai", "gemini"],
        help="Provedor da tabela vetorial para remocao.",
    )

    # Compatibilidade com flags curtas pedidas inicialmente.
    parser.add_argument("-f", "--file", help="Atalho para `ingest --file`.")
    parser.add_argument("-c", "--chat", metavar="MESSAGE", help="Atalho para `chat --message`.")
    parser.add_argument(
        "-m",
        "--model",
        choices=["openai", "gemini"],
        help="Provedor global para atalhos `-f` e `-c`.",
    )

    args = parser.parse_args()

    if args.command == "config":
        config = configure_interactive()
        print(f"Configuracao salva para banco {config.pg_host}:{config.pg_port}.")
        return 0

    if args.command == "ingest":
        from ingest import ingest_pdf

        chunks_count = ingest_pdf(args.file, provider=args.model)
        print(f"Ingestao concluida. Chunks inseridos: {chunks_count}")
        return 0

    if args.command == "search":
        from search import semantic_search

        items = semantic_search(args.query, k=args.k, provider=args.model)
        for item in items:
            print(f"[id={item['id']}] source={item['source']} distance={item['distance']:.4f}")
            print(item["snippet"])
            print("-" * 80)
        if not items:
            print("Nenhum resultado encontrado.")
        return 0

    if args.command == "chat":
        from chat import ask_once, interactive_chat

        if args.message:
            print(ask_once(args.message, top_k=args.k, provider=args.model))
        else:
            interactive_chat(top_k=args.k, provider=args.model)
        return 0

    if args.command == "delete":
        from delete import delete_documents

        if args.id is None and not args.source:
            parser.error("No comando `delete`, informe --id ou --source.")

        deleted = delete_documents(doc_id=args.id, source=args.source, provider=args.model)
        print(f"Documentos removidos: {deleted}")
        return 0

    if args.command == "list":
        from list_docs import list_documents

        items = list_documents(
            provider=args.model,
            limit=args.limit,
            offset=args.offset,
            source_contains=args.source_contains,
        )
        if not items:
            print("Nenhum documento encontrado.")
            return 0
        for item in items:
            print(f"[id={item['id']}]")
            print(f"source={item['source']}")
            print("-" * 80)
        return 0

    if args.file:
        from ingest import ingest_pdf

        chunks_count = ingest_pdf(args.file, provider=args.model)
        print(f"Ingestao concluida. Chunks inseridos: {chunks_count}")
        return 0

    if args.chat:
        from chat import ask_once

        print(ask_once(args.chat, provider=args.model))
        return 0

    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

