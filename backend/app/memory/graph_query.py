"""
Query ke Cognee knowledge graph (Cloud API) - dipakai buat pertanyaan yang butuh
konteks relasional (bukan sekadar kemiripan teks biasa).
"""

import requests

from app.core.config import settings

DATASET_NAME = "aspripay_kb"


def ask_graph(question: str, top_k: int = 5) -> str:
    """
    Cari jawaban dari knowledge graph Cognee lewat Cloud API.
    Return teks jawaban bersih -- ini yang dikirim ke widget/frontend nantinya.
    """
    resp = requests.post(
        f"{settings.COGNEE_BASE_URL}/api/v1/search",
        json={
            "query": question,
            "searchType": "GRAPH_COMPLETION",
            "datasets": [DATASET_NAME],
            "topK": top_k,
        },
        headers={
            "Content-Type": "application/json",
            "X-Api-Key": settings.COGNEE_API_KEY,
        },
    )
    if not resp.ok:
        print(f"  [ERROR {resp.status_code}] {resp.text}")
    resp.raise_for_status()
    result = resp.json()

    # Response Cognee: list berisi dict, dict-nya punya key "search_result" (list of string)
    if isinstance(result, list) and result:
        result = result[0]

    if isinstance(result, dict) and "search_result" in result:
        search_result = result["search_result"]
        if isinstance(search_result, list) and search_result:
            return str(search_result[0])
        return str(search_result)

    return str(result)