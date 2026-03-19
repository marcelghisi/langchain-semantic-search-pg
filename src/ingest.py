from __future__ import annotations

import argparse
from pathlib import Path

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from langchain_postgres import PGVector

from common import (
    build_postgres_connection_string,
    get_embeddings_provider,
    load_config,
    resolve_provider,
    table_name_for_provider,
)

def prepare_enriched_docs(pdf_path: Path) -> list[Document]:
    pdf_path = Path(pdf_path).expanduser().resolve()
    loader = PyPDFLoader(file_path=str(pdf_path))
    pages = loader.load()
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000, chunk_overlap=150, add_start_index=False
    ).split_documents(pages)
    if not text_splitter:
        raise ValueError("Nao foi possivel dividir o texto do PDF.")
    enriched_docs = [
        Document(
            page_content=doc.page_content,
            metadata={k: v for k, v in doc.metadata.items() if v not in ("", None)},
        )
        for doc in text_splitter
    ]
    return enriched_docs

def extract_pdf_text(pdf_path: Path) -> str:
    pdf_path = Path(pdf_path).expanduser().resolve()
    loader = PyPDFLoader(file_path=str(pdf_path))
    pages = loader.load()
    text = "\n".join((page.page_content or "") for page in pages).strip()
    if not text:
        raise ValueError("Nao foi possivel extrair texto do PDF.")
    return text


def ingest_pdf(file_path: str, provider: str | None = None) -> int:
    config = load_config()
    selected_provider = resolve_provider(config, provider)
    pdf_path = Path(file_path).expanduser().resolve()
    if not pdf_path.exists():
        raise FileNotFoundError(f"Arquivo nao encontrado: {pdf_path}")
    
    enriched_docs = prepare_enriched_docs(pdf_path)
    
    embeddings = get_embeddings_provider(config, selected_provider)

    vector_store = PGVector(
        embeddings=embeddings,
        collection_name=table_name_for_provider(selected_provider),
        connection=build_postgres_connection_string(config),
    )

    vector_store.add_documents(enriched_docs)
    return len(enriched_docs)


def main() -> int:
    parser = argparse.ArgumentParser(description="Ingestao de PDF no pgvector.")
    parser.add_argument(
        "--file",
        default="document.pdf",
        help="Caminho do PDF para ingestao (default: document.pdf).",
    )
    parser.add_argument(
        "-m",
        "--model",
        choices=["openai", "gemini"],
        help="Provedor de modelo para embeddings.",
    )
    args = parser.parse_args()

    chunks_count = ingest_pdf(args.file, provider=args.model)
    print(f"Ingestao concluida. Chunks inseridos: {chunks_count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

