"""Verification script testing real Moss retrieval against critical technician queries."""

import asyncio
import sys

from app.config.settings import settings
from app.retrieval.moss import MossRetrievalProvider


CRITICAL_QUERIES = [
    {
        "name": "Query 1: Active Error Code & Measurement",
        "query": "I'm getting E17 again on unit 017. Pressure is around 195 PSI.",
        "expected_docs": ["e17-troubleshooting", "unit-017-service-record", "acx420-troubleshooting-guide"],
        "filters": None,
    },
    {
        "name": "Query 2: Follow-up on Past Replacement & Next Diagnostic Steps",
        "query": "The pressure sensor was already replaced last month. What should I check next?",
        "expected_docs": ["unit-017-service-record", "e17-troubleshooting", "acx420-troubleshooting-guide"],
        "filters": None,
    },
    {
        "name": "Query 3: Safety Procedures Before Pressure System Inspection",
        "query": "What safety procedure applies before checking the pressure system?",
        "expected_docs": ["pressure-safety-sop"],
        "filters": None,
    },
]


async def run_verification() -> bool:
    print("=" * 60)
    print("RELAY MOSS RETRIEVAL VERIFICATION")
    print("=" * 60)
    print(f"Index Name: {settings.moss_index_name}")
    print(f"Project ID: {settings.moss_project_id[:8]}... (configured)")
    print(f"Default Alpha: {settings.moss_hybrid_alpha}")

    provider = MossRetrievalProvider()

    if not provider.is_configured():
        print("ERROR: Moss credentials are not configured!", file=sys.stderr)
        return False

    print("\nLoading Moss index into memory...")
    try:
        await provider.load()
    except Exception as e:
        print(f"ERROR: Failed to load Moss index: {e}", file=sys.stderr)
        return False

    print(f"Provider Status: {provider.status.upper()}")
    all_passed = True

    for item in CRITICAL_QUERIES:
        print("\n" + "-" * 50)
        print(f"Executing: {item['name']}")
        print(f"Query: \"{item['query']}\"")

        try:
            resp = await provider.search(
                query=item["query"],
                filters=item.get("filters"),
                limit=5,
            )

            print(f"Status: SUCCESS | Provider: {resp.provider}")
            print(f"Latency: {resp.latency_ms} ms (Actual measured)")
            print(f"Results Returned: {len(resp.results)}")
            print("Retrieved Documents:")

            retrieved_ids = []
            for rank, res in enumerate(resp.results, 1):
                score_str = f"{res.score:.4f}" if res.score is not None else "N/A"
                print(f"  {rank}. [{score_str}] ID: {res.chunk_id}")
                print(f"     Title: {res.title} | Source: {res.source}")
                retrieved_ids.append(res.chunk_id)

            # Check if any expected relevant document is in the result set
            found_expected = any(exp_id in retrieved_ids for exp_id in item["expected_docs"])
            if found_expected:
                print("  => Relevant Evidence Grounding: VERIFIED")
            else:
                print(f"  => WARNING: None of {item['expected_docs']} in top results: {retrieved_ids}")
                all_passed = False

        except Exception as e:
            print(f"Query execution FAILED: {e}", file=sys.stderr)
            all_passed = False

    print("\n" + "=" * 60)
    if all_passed:
        print("VERIFICATION: PASSED (All critical scenarios grounded)")
        print("=" * 60)
        return True
    else:
        print("VERIFICATION: FAILED")
        print("=" * 60)
        return False


def main():
    success = asyncio.run(run_verification())
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
