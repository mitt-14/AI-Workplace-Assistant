from __future__ import annotations

from app.rag.keyword_retriever import keyword_search
from app.rag.retriever import semantic_search


DOCUMENT_ID = "547339ae-43e8-4556-9398-f2d39747d3c3"

TEST_QUERIES = [
    "vacation days",
    "How much annual leave do employees receive?",
    "MFA password requirements",
    "When should a security incident be reported?",
    "RTO for critical services",
]


def print_results(
    search_type: str,
    results: list[dict],
) -> None:
    print(f"\n{search_type}")
    print("=" * 80)

    if not results:
        print("No results returned.")
        return

    for position, result in enumerate(results, start=1):
        score = result.get(
            "keyword_score",
            result.get("relevance_score"),
        )

        print(f"\nResult {position}")
        print(f"Filename: {result.get('filename')}")
        print(f"Page: {result.get('page_number')}")
        print(f"Chunk: {result.get('chunk_index')}")
        print(f"Score: {score}")
        print(f"Text: {result.get('text', '')[:300]}")
        print("-" * 80)


def main() -> None:
    for query in TEST_QUERIES:
        print("\n\n")
        print("#" * 100)
        print(f"QUERY: {query}")
        print("#" * 100)

        keyword_results = keyword_search(
            query=query,
            top_k=3,
            document_id=DOCUMENT_ID,
        )

        semantic_results = semantic_search(
            query=query,
            top_k=3,
            document_id=DOCUMENT_ID,
        )

        print_results(
            "BM25 KEYWORD SEARCH",
            keyword_results,
        )

        print_results(
            "SEMANTIC SEARCH",
            semantic_results,
        )


if __name__ == "__main__":
    main()