"""Benchmark: HeadingChunker + RAPTOR-style hierarchical roll-up (src/hierarchical.py)
vs. the flat HeadingChunker/RecursiveChunker runs.

Uses its own Chroma persist directory (./chroma_data/hierarchical_r3) so it never
touches the group's default store (./chroma_data) or the personal flat-HeadingChunker
store (./chroma_data/r3_real).

Real OpenAI embeddings + a real OpenAI chat model for the roll-up summaries — this
calls the API for every summarized group, so it costs a handful of extra requests
per run.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.chroma_store import ChromaEmbeddingStore
from src.chunking import HeadingChunker, compute_similarity
from src.embeddings import OpenAIEmbedder
from src.hierarchical import MultiLevelChunker, OpenAISummarizer
from src.models import Document

DATA = ROOT / "data" / "scholarship"
PERSIST_DIR = "./chroma_data/hierarchical_r3"
FRONT = re.compile(r"^---\s*\n(.*?)\n---\s*\n?(.*)$", re.S)

QUERIES = [
    ("Số suất và giá trị Green Tech", "Học bổng Green Tech 2026 có bao nhiêu suất, giá trị bao nhiêu và kéo dài bao lâu?", None, ["18,000,000", "6 months"]),
    ("Mốc thời gian Green Tech", "Hạn cuối nộp hồ sơ học bổng Green Tech 2026 là ngày nào và thời gian dự kiến bắt đầu là khi nào?", None, ["March 23, 2026", "April 2026"]),
    ("Quy trình", "Quy trình xét học bổng và hỗ trợ tài chính của USTH gồm những bước nào?", None, ["Step 1", "Step 2", "Step 3"]),
    ("Quỹ học bổng 2026-2027", "Trong năm học 2026-2027, USTH dự kiến dành bao nhiêu tiền cho quỹ học bổng và áp dụng cho những nhóm người học nào?", None, ["VND 16 billion", "undergraduate"]),
    ("Đối tượng quy định 2026", "Đối tượng sinh viên nào được áp dụng các quy định học bổng năm 2026 của USTH?", {"audience": "student"}, ["Vietnamese students", "international students"]),
]


def parse_file(path: Path) -> tuple[dict, str]:
    raw = path.read_text(encoding="utf-8")
    match = FRONT.match(raw)
    if not match:
        return {}, raw
    metadata: dict = {}
    for line in match.group(1).splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        metadata[key.strip()] = value.strip().strip('"')
    return metadata, match.group(2).strip()


def build_stores():
    load_dotenv(override=False)
    embedder = OpenAIEmbedder()
    summarizer = OpenAISummarizer()
    base_chunker = HeadingChunker(chunk_size=500, overlap=50)
    mlc = MultiLevelChunker(base_chunker=base_chunker, summarize_fn=summarizer, group_sizes=[5])

    store_l1 = ChromaEmbeddingStore("hier_level1", embedding_fn=embedder, persist_directory=PERSIST_DIR)
    store_l2 = ChromaEmbeddingStore("hier_level2", embedding_fn=embedder, persist_directory=PERSIST_DIR)

    l1_count = 0
    l2_count = 0
    for path in sorted(DATA.glob("*.md")):
        metadata, body = parse_file(path)
        doc_id = path.stem
        metadata["doc_id"] = doc_id
        levels = mlc.build_levels(body)

        l1_docs = [
            Document(
                id=f"{doc_id}#L1#{item['chunk_index']}",
                content=item["content"],
                metadata={**metadata, "level": 1, "chunk_index": item["chunk_index"]},
            )
            for item in levels.get(1, [])
        ]
        store_l1.add_documents(l1_docs)
        l1_count += len(l1_docs)

        l2_items = levels.get(2, [])
        l2_docs = [
            Document(
                id=f"{doc_id}#L2#{item['chunk_index']}",
                content=item["content"],
                metadata={
                    **metadata,
                    "level": 2,
                    "chunk_index": item["chunk_index"],
                    "group_index": json.dumps(item["group_index"]),
                },
            )
            for item in l2_items
        ]
        if l2_docs:
            store_l2.add_documents(l2_docs)
        l2_count += len(l2_docs)

    return embedder, store_l1, store_l2, l1_count, l2_count


def drill_down(
    embedder,
    store_l1,
    store_l2,
    question: str,
    metadata_filter: dict | None,
    top_k: int = 3,
    summary_beam: int = 3,
) -> list[dict]:
    """Search level-2 summaries first, then re-rank only their child level-1 chunks (narrow to top_k).

    `summary_beam` is intentionally tunable and defaults to `top_k` (narrow):
    tried widening it to 9 to rescue Q3 ("Quy trình...", whose correct summary
    ranks 9th/15 for that query), but on this 8-document corpus a wider beam pulls
    in enough extra level-1 candidates that the final flat rerank behaves like a
    plain corpus-wide search again — which loses the two queries (Green Tech Q1/Q2)
    that a narrow beam of 3 got right by keeping the candidate pool small and
    on-topic. Net effect measured: beam=3 -> 4/5 queries correct, beam=9 -> 3/5.
    Kept at 3 because it wins more than it loses on this corpus; see
    report/REPORT_CANHAN.md section 5 for the full trade-off writeup.
    """
    l2_hits = store_l2.search_with_filter(question, top_k=summary_beam, metadata_filter=metadata_filter)
    if not l2_hits:
        return store_l1.search_with_filter(question, top_k=top_k, metadata_filter=metadata_filter)

    candidate_ids = []
    for hit in l2_hits:
        doc_id = hit["metadata"]["doc_id"]
        group = json.loads(hit["metadata"]["group_index"])
        candidate_ids.extend(f"{doc_id}#L1#{ci}" for ci in group)

    raw = store_l1._collection.get(ids=candidate_ids, include=["documents", "metadatas", "embeddings"])
    query_embedding = embedder(question)
    reranked = []
    for content, metadata, embedding in zip(raw["documents"], raw["metadatas"], raw["embeddings"]):
        if metadata_filter and any(metadata.get(k) != v for k, v in metadata_filter.items()):
            continue
        score = compute_similarity(query_embedding, list(embedding))
        reranked.append({"content": content, "metadata": metadata, "score": score})
    reranked.sort(key=lambda r: r["score"], reverse=True)
    return reranked[:top_k]


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    embedder, store_l1, store_l2, l1_count, l2_count = build_stores()
    print(f"Embedding backend: {embedder._backend_name}")
    print(f"Level-1 (base HeadingChunker) chunks: {l1_count}")
    print(f"Level-2 (LLM roll-up summary) chunks: {l2_count}")
    print(f"Persist dir: {PERSIST_DIR}\n")

    hits = 0
    for number, (title, question, metadata_filter, gold_markers) in enumerate(QUERIES, 1):
        print(f"=== Query {number}: {title} ===")
        print(question)
        results = drill_down(embedder, store_l1, store_l2, question, metadata_filter)
        for rank, r in enumerate(results, 1):
            content = r["content"].replace("\n", " ")
            print(f"  {rank}. score={r['score']:.4f} doc={r['metadata'].get('doc_id')}")
            print(f"     {content[:200]}")
        joined = " ".join(r["content"] for r in results)
        found = [marker for marker in gold_markers if marker.lower() in joined.lower()]
        print(f"Gold markers found in top-3: {found} / {gold_markers}")
        if found:
            hits += 1
        print()

    print(f"TOTAL queries with >=1 gold marker in top-3: {hits}/5")


if __name__ == "__main__":
    main()
