from __future__ import annotations

import os
from typing import Callable

from .models import Document
from .store import EmbeddingStore

LLM_PROVIDER_ENV = "LLM_PROVIDER"
OPENAI_CHAT_MODEL = "gpt-4o-mini"
GEMINI_CHAT_MODEL = "gemini-2.0-flash"

DEFAULT_GROUP_SIZES = [5, 3, 3, 3]

SummarizeFn = Callable[[list[str]], str]


class OpenAISummarizer:
    """Summarizes a group of chunks into one parent chunk via the OpenAI Chat API."""

    def __init__(self, model_name: str = OPENAI_CHAT_MODEL) -> None:
        from openai import OpenAI

        self.model_name = model_name
        self.client = OpenAI()

    def __call__(self, texts: list[str]) -> str:
        joined = "\n\n".join(texts)
        response = self.client.chat.completions.create(
            model=self.model_name,
            temperature=0,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Tóm tắt ngắn gọn các đoạn văn bản sau thành một đoạn duy nhất. "
                        "Giữ lại số liệu, mốc thời gian và điều khoản quan trọng, không bịa thêm thông tin."
                    ),
                },
                {"role": "user", "content": joined},
            ],
        )
        return response.choices[0].message.content.strip()


class GeminiSummarizer:
    """Summarizes a group of chunks into one parent chunk via the Gemini API."""

    def __init__(self, model_name: str = GEMINI_CHAT_MODEL) -> None:
        from google import genai

        api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise RuntimeError("GEMINI_API_KEY (or GOOGLE_API_KEY) is required for GeminiSummarizer")
        self.model_name = model_name
        self.client = genai.Client(api_key=api_key)

    def __call__(self, texts: list[str]) -> str:
        joined = "\n\n".join(texts)
        prompt = (
            "Tóm tắt ngắn gọn các đoạn văn bản sau thành một đoạn duy nhất. "
            "Giữ lại số liệu, mốc thời gian và điều khoản quan trọng, không bịa thêm thông tin.\n\n"
            f"{joined}"
        )
        response = self.client.models.generate_content(model=self.model_name, contents=prompt)
        return response.text.strip()


def resolve_summarizer() -> SummarizeFn:
    """Pick a summarizer from LLM_PROVIDER env var ("openai" default, or "gemini")."""
    provider = os.getenv(LLM_PROVIDER_ENV, "openai").strip().lower()
    if provider == "gemini":
        return GeminiSummarizer()
    return OpenAISummarizer()


class MultiLevelChunker:
    """
    Build a RAPTOR-style chunk hierarchy on top of any base chunker.

    Equivalent to `hierarchical_chunking()` in the old embedding.py, minus the
    file-based backup/resume cache (this lab's corpora are small enough that a
    single run is cheap).
    """

    def __init__(
        self,
        base_chunker,
        summarize_fn: SummarizeFn,
        group_sizes: list[int] | None = None,
    ) -> None:
        self.base_chunker = base_chunker
        self.summarize_fn = summarize_fn
        self.group_sizes = list(DEFAULT_GROUP_SIZES if group_sizes is None else group_sizes)

    def build_levels(self, text: str) -> dict[int, list[dict]]:
        """
        Returns {level: [{"content", "chunk_index", "group_index"}, ...]}.

        Level 1 items have group_index=None (they are leaves). Level N>1 items
        have group_index = the list of level-(N-1) chunk_index values they
        summarize.
        """
        base_chunks = self.base_chunker.chunk(text)
        levels: dict[int, list[dict]] = {
            1: [
                {"content": content, "chunk_index": i, "group_index": None}
                for i, content in enumerate(base_chunks)
            ]
        }

        current = levels[1]
        for level_num, group_size in enumerate(self.group_sizes, start=2):
            if len(current) <= 1:
                break

            next_level: list[dict] = []
            for new_index, i in enumerate(range(0, len(current), group_size)):
                group = current[i : i + group_size]
                summary = self.summarize_fn([item["content"] for item in group])
                next_level.append(
                    {
                        "content": summary,
                        "chunk_index": new_index,
                        "group_index": [item["chunk_index"] for item in group],
                    }
                )
            levels[level_num] = next_level
            current = next_level

        return levels


class MultiLevelStore:
    """
    One in-memory EmbeddingStore per level, plus drill-down retrieval.

    Equivalent to HierarchicalRetriever.retrieve_across_level in
    `Hierachical chunking/LinaNovel/hierarchical_retriever.py`: search the
    highest level first, follow each hit's group_index down to the next level,
    restrict the search there to only those indices, and repeat until
    low_level is reached.
    """

    def __init__(self, doc_id: str, levels: dict[int, list[dict]], embedding_fn=None) -> None:
        self.doc_id = doc_id
        self.stores: dict[int, EmbeddingStore] = {}
        for level_num, items in levels.items():
            store = EmbeddingStore(collection_name=f"{doc_id}_level_{level_num}", embedding_fn=embedding_fn)
            docs = [
                Document(
                    id=f"{doc_id}#L{level_num}#{item['chunk_index']}",
                    content=item["content"],
                    metadata={
                        "doc_id": doc_id,
                        "level": level_num,
                        "chunk_index": item["chunk_index"],
                        "group_index": item["group_index"],
                    },
                )
                for item in items
            ]
            store.add_documents(docs)
            self.stores[level_num] = store

    def _candidates(self, level_num: int, allowed_indices: list[int] | None) -> list[dict]:
        store = self.stores.get(level_num)
        if store is None:
            return []
        if allowed_indices is None:
            return store._store
        return [r for r in store._store if r["metadata"]["chunk_index"] in allowed_indices]

    def retrieve_across_level(self, query: str, high_level: int, low_level: int, top_k: int = 3) -> list[dict]:
        """Drill down from a high (summary) level to a low (detail) level."""
        if low_level >= high_level:
            raise ValueError("high_level phải lớn hơn low_level")

        allowed_indices: list[int] | None = None
        for level_num in range(high_level, low_level, -1):
            store = self.stores.get(level_num)
            if store is None:
                continue
            candidates = self._candidates(level_num, allowed_indices)
            results = store._search_records(query, candidates, top_k)
            if not results:
                return []
            allowed_indices = []
            for r in results:
                group = r["metadata"].get("group_index")
                if group:
                    allowed_indices.extend(group)

        final_store = self.stores.get(low_level)
        if final_store is None:
            return []
        candidates = self._candidates(low_level, allowed_indices)
        return final_store._search_records(query, candidates, top_k)
