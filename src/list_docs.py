from __future__ import annotations

import argparse
from typing import Any

from common import (
    load_config,
    open_connection,
    resolve_provider,
    table_name_for_provider,
)


def list_documents(
    *,
    provider: str | None = None,
    limit: int = 20,
    offset: int = 0,
    source_contains: str | None = None,
) -> list[dict[str, Any]]:
    config = load_config()
    selected_provider = resolve_provider(config, provider)
    collection_name = table_name_for_provider(selected_provider)

    where_clause = "WHERE c.name = %s"
    params: list[object] = [collection_name]
    if source_contains:
        where_clause += " AND e.cmetadata->>'source' ILIKE %s"
        params.append(f"%{source_contains}%")

    params.extend([limit, offset])

    with open_connection(config) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                f"""
                SELECT
                    e.id::text AS id,
                    COALESCE(e.cmetadata->>'source', '') AS source
                FROM langchain_pg_embedding e
                JOIN langchain_pg_collection c ON c.uuid = e.collection_id
                {where_clause}
                ORDER BY e.id DESC
                LIMIT %s OFFSET %s
                """,
                params,
            )
            rows = cursor.fetchall()

    results: list[dict[str, Any]] = []
    for row in rows:
        results.append(
            {
                "id": str(row[0]),
                "source": str(row[1]),
            }
        )
    return results


def main() -> int:
    parser = argparse.ArgumentParser(description="Lista documentos ingeridos no pgvector.")
    parser.add_argument(
        "-m",
        "--model",
        choices=["openai", "gemini"],
        help="Provedor da tabela vetorial.",
    )
    parser.add_argument("--limit", type=int, default=20, help="Quantidade maxima de itens.")
    parser.add_argument("--offset", type=int, default=0, help="Quantidade de itens para pular.")
    parser.add_argument(
        "--source-contains",
        help="Filtra por parte do caminho source.",
    )
    args = parser.parse_args()

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


if __name__ == "__main__":
    raise SystemExit(main())

