import re
from typing import List, Dict
from dotenv import load_dotenv
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from langchain_core.vectorstores import InMemoryVectorStore
from langchain_google_genai import GoogleGenerativeAIEmbeddings

load_dotenv()

# Text splitter configured for optimal chunk size & semantic boundaries
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=150,
    separators=["\n\n", "\n", ". ", " ", ""],
)


def _keyword_relevance_score(text: str, keywords: List[str]) -> float:
    """Fallback ranking score based on term frequencies and density."""
    if not text or not keywords:
        return 0.0
    text_lower = text.lower()
    score = 0.0
    for kw in keywords:
        kw_clean = kw.lower().strip()
        if len(kw_clean) > 2:
            count = text_lower.count(kw_clean)
            score += count * 1.5
    # Bonus for numbers/statistics (indicates concrete benchmarks)
    numbers = len(re.findall(r"\b\d+(\.\d+)?%?\b", text))
    score += min(numbers * 0.5, 3.0)
    return score


def extract_top_chunks(
    pages: List[Dict[str, str]],
    topic: str,
    sub_queries: List[str],
    top_k: int = 10,
) -> str:
    """
    Ingests full-text web pages, chunks them semantically, indexes them into
    an in-memory vector store, and retrieves the top-K most information-dense chunks.
    """
    if not pages:
        return "No page content available."

    all_docs: List[Document] = []

    # 1. Chunk full pages while preserving source URL metadata
    for page in pages:
        url = page.get("url", "")
        raw_text = page.get("text", "")
        if not raw_text or len(raw_text.strip()) < 50:
            continue

        chunks = text_splitter.split_text(raw_text)
        for chunk in chunks:
            if len(chunk.strip()) > 80:  # ignore tiny snippets
                all_docs.append(Document(page_content=chunk.strip(), metadata={"source": url}))

    if not all_docs:
        return "No meaningful content extracted from pages."

    selected_docs: List[Document] = []
    seen_contents = set()

    # 2. Pre-filter candidate chunks to stay safely within Gemini Free Tier (100 req/min limit)
    search_terms = re.findall(r"\w+", f"{topic} {' '.join(sub_queries)}".lower())
    candidate_docs = sorted(
        all_docs,
        key=lambda d: _keyword_relevance_score(d.page_content, search_terms),
        reverse=True,
    )[:35]

    # 3. Try Vector Similarity Search with Gemini Embeddings on the high-signal candidates
    try:
        embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")
        vector_store = InMemoryVectorStore.from_documents(candidate_docs, embeddings)

        queries_to_search = [topic] + [q for q in sub_queries if q.strip()]

        for query in queries_to_search:
            # Fetch top matches per query angle
            matches = vector_store.similarity_search(query, k=3)
            for doc in matches:
                key = doc.page_content[:100]
                if key not in seen_contents:
                    seen_contents.add(key)
                    selected_docs.append(doc)
                if len(selected_docs) >= top_k:
                    break
            if len(selected_docs) >= top_k:
                break

    except Exception as e:
        print(f"[RAG Warning] Vector search fallback triggered: {e}")
        # 3. Robust Keyword/BM25-style Fallback
        search_terms = re.findall(r"\w+", f"{topic} {' '.join(sub_queries)}".lower())
        ranked_docs = sorted(
            all_docs,
            key=lambda d: _keyword_relevance_score(d.page_content, search_terms),
            reverse=True,
        )
        for doc in ranked_docs:
            key = doc.page_content[:100]
            if key not in seen_contents:
                seen_contents.add(key)
                selected_docs.append(doc)
            if len(selected_docs) >= top_k:
                break

    if not selected_docs:
        selected_docs = all_docs[:top_k]

    # Format into structured evidence for the Writer
    formatted_chunks = []
    for idx, doc in enumerate(selected_docs[:top_k], 1):
        source = doc.metadata.get("source", "Unknown Source")
        formatted_chunks.append(
            f"--- Excerpt {idx} (Source: {source}) ---\n{doc.page_content}\n"
        )

    return "\n".join(formatted_chunks)
