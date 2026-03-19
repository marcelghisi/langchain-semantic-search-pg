from __future__ import annotations

import argparse
from typing import Any

from langchain_google_genai import ChatGoogleGenerativeAI
from openai import OpenAI

from common import DEFAULT_TEMPERATURES, load_config, resolve_provider
from search import semantic_search


def build_context(results: list[dict[str, Any]]) -> str:
    if not results:
        return "Sem contexto encontrado."
    blocks = []
    for item in results:
        blocks.append(f"Fonte: {item['source']}\nTrecho: {item['snippet']}")
    return "\n\n".join(blocks)


def ask_once(question: str, top_k: int = 10, provider: str | None = None) -> str:
    config = load_config()
    selected_provider = resolve_provider(config, provider)
    docs = semantic_search(question, k=top_k, provider=selected_provider)
    context = build_context(docs)

    system_prompt = (
        "Voce deve responder SOMENTE com base no contexto fornecido. "
        "Nao use conhecimento externo. "
        "Se a resposta nao estiver explicitamente no contexto, responda exatamente: "
        "'Nao encontrei essa informacao no contexto recuperado.'"
    )
    
    user_prompt = f"Contexto:\n{context}\n\nPergunta: {question}"

    if selected_provider == "openai":
        client = OpenAI(api_key=config.openai_api_key)
        completion = client.chat.completions.create(
            model=config.openai_llm_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=DEFAULT_TEMPERATURES[config.openai_llm_model],
        )
        return completion.choices[0].message.content or ""

    llm = ChatGoogleGenerativeAI(
        model=config.gemini_llm_model,
        google_api_key=config.google_api_key,
        temperature=0.1,
    )
    response = llm.invoke(
        f"{system_prompt}\n\n{user_prompt}"
    )
    return str(response.content)


def interactive_chat(top_k: int = 3, provider: str | None = None) -> None:
    print("Chat iniciado. Digite 'sair' para encerrar.")
    while True:
        question = input("\nVoce: ").strip()
        if not question:
            continue
        if question.lower() in {"sair", "exit", "quit"}:
            break
        answer = ask_once(question, top_k=top_k, provider=provider)
        print(f"\nGhisi: {answer}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Chat com contexto do pgvector.")
    parser.add_argument("--message", help="Pergunta unica.")
    parser.add_argument("--k", type=int, default=3, help="Top K resultados do contexto.")
    parser.add_argument(
        "-m",
        "--model",
        choices=["openai", "gemini"],
        help="Provedor de modelo para responder.",
    )
    args = parser.parse_args()

    if args.message:
        print(ask_once(args.message, top_k=args.k, provider=args.model))
    else:
        interactive_chat(top_k=args.k, provider=args.model)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

