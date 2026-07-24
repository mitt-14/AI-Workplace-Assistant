from app.rag.hybrid_retriever import hybrid_search


DOCUMENT_ID = "547339ae-43e8-4556-9398-f2d39747d3c3"


def main() -> None:
    queries = [
        "vacation days",
        "MFA password requirements",
        "When should a security incident be reported?",
        "RTO for critical services",
    ]

    for query in queries:
        print("\n" + "#" * 100)
        print(f"QUERY: {query}")
        print("#" * 100)

        results = hybrid_search(
            query=query,
            top_k=5,
            document_id=DOCUMENT_ID,
        )

        for position, result in enumerate(results, start=1):
            print(f"\nResult {position}")
            print(f"Page: {result.get('page_number')}")
            print(f"Chunk: {result.get('chunk_index')}")
            print(
                "Methods:",
                result.get("retrieval_methods"),
            )
            print(
                "Semantic:",
                result.get("normalized_semantic_score"),
            )
            print(
                "Keyword:",
                result.get("normalized_keyword_score"),
            )
            print(
                "Hybrid:",
                result.get("hybrid_score"),
            )
            print(
                "Text:",
                result.get("text", "")[:300],
            )
            print("-" * 80)


if __name__ == "__main__":
    main()