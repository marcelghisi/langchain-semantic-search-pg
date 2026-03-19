from __future__ import annotations

import argparse
from typing import Any

from common import (
    build_postgres_connection_string,
    get_embeddings_provider,
    load_config,
    resolve_provider,
    table_name_for_provider,
)
from langchain_postgres import PGVector


def semantic_search(
    query: str,
    k: int = 10,
    provider: str | None = None,
) -> list[dict[str, Any]]:
    config = load_config()
    selected_provider = resolve_provider(config, provider)
    vector_store = PGVector(
        embeddings=get_embeddings_provider(config, selected_provider),
        collection_name=table_name_for_provider(selected_provider),
        connection=build_postgres_connection_string(config),
    )
    rows = vector_store.similarity_search_with_score(query, k=k)

    results: list[dict[str, Any]] = []
    for row in rows:
        doc, score = row
        results.append(
            {
                "id": doc.id,
                "source": doc.metadata.get("source"),
                "snippet": doc.page_content[:500],
                "distance": float(score),
            }
        )
    return results


def main() -> int:
    parser = argparse.ArgumentParser(description="Busca semantica no pgvector.")
    parser.add_argument("query", help="Texto da consulta semantica.")
    parser.add_argument("--k", type=int, default=3, help="Numero de resultados.")
    parser.add_argument(
        "-m",
        "--model",
        choices=["openai", "gemini"],
        help="Provedor de modelo para embeddings.",
    )
    args = parser.parse_args()

    items = semantic_search(args.query, args.k, provider=args.model)
    if not items:
        print("Nenhum documento encontrado.")
        return 0

    for item in items:
        print(f"[id={item['id']}] source={item['source']} distance={item['distance']:.4f}")
        print(item["snippet"])
        print("-" * 80)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

