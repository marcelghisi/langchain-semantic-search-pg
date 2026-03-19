from __future__ import annotations

import argparse
from pathlib import Path

from common import (
    load_config,
    open_connection,
    resolve_provider,
    table_name_for_provider,
)


def delete_documents(
    *,
    doc_id: str | None = None,
    source: str | None = None,
    provider: str | None = None,
) -> int:
    if doc_id is None and not source:
        raise ValueError("Informe --id ou --source para excluir documentos.")

    config = load_config()
    selected_provider = resolve_provider(config, provider)
    collection_name = table_name_for_provider(selected_provider)

    conditions: list[str] = []
    params: list[object] = [collection_name]

    if doc_id is not None:
        conditions.append("e.id::text = %s")
        params.append(doc_id)
    if source:
        normalized_source = str(Path(source).expanduser().resolve())
        if normalized_source == source:
            conditions.append("e.cmetadata->>'source' = %s")
            params.append(source)
        else:
            # Aceita tanto o valor bruto quanto o caminho normalizado.
            conditions.append("(e.cmetadata->>'source' = %s OR e.cmetadata->>'source' = %s)")
            params.extend([source, normalized_source])

    where_clause = " AND ".join(conditions)

    with open_connection(config) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                f"""
                DELETE FROM langchain_pg_embedding e
                USING langchain_pg_collection c
                WHERE e.collection_id = c.uuid
                  AND c.name = %s
                  AND {where_clause}
                """,
                params,
            )
            deleted_count = cursor.rowcount
        connection.commit()

    return max(deleted_count, 0)


def main() -> int:
    parser = argparse.ArgumentParser(description="Exclusao de documentos do pgvector.")
    parser.add_argument("--id", help="ID do documento para excluir.")
    parser.add_argument("--source", help="Source (caminho) para excluir.")
    parser.add_argument(
        "-m",
        "--model",
        choices=["openai", "gemini"],
        help="Provedor de tabela vetorial.",
    )
    args = parser.parse_args()
    if args.id is None and not args.source:
        parser.error("Informe --id ou --source.")

    deleted = delete_documents(doc_id=args.id, source=args.source, provider=args.model)
    print(f"Documentos removidos: {deleted}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

