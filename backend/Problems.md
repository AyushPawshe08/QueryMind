0. the problem we were facing was that if the critic score was below 7 we searched the whole topic again resulting repeated same searches
Solution -> We will search only the deficienes instead of whole research topic again

1. We searched the whole topic which sometime return vague results so tought of query decomposition which mean we will break the query into sub-query and search the sub-queries
Solution -> Sub-Query Decomposition (Planner): Deconstructs any complex research subject into 3 orthogonal sub-topics (e.g., Foundations/Architecture, Real-World Benchmarks, Key Challenges & Future Outlook) to gather multi-faceted intelligence.

2. The Current Issue: tools/scrape.py  naively slices raw text at [:3000]. This often clips crucial conclusions, tables, or sections located near the bottom of long whitepapers.
The Upgrade -> Ingest full scraped pages → split using RecursiveCharacterTextSplitter.
Store chunks in an in-memory vector database (ChromaDB or FAISS).
Use BM25 + Semantic Hybrid Search or a Cross-Encoder Reranker (e.g. Cohere or FlashRank) to pull only the top 10 most information-dense paragraphs into the Writer prompt.


3. The Current Issue: requests.get fails on JavaScript-rendered Single Page Applications (React, Next.js, Vue) and triggers 403 Forbidden errors on sites guarded by Cloudflare.
The Upgrade:
Replace or augment requests with Crawl4AI
 (open-source LLM-friendly crawler) or Playwright.
Automatically extracts clean Markdown, extracts tables as structured JSON/Markdown, and bypasses JavaScript rendering.


4. Dynamic Chart & Diagram Generation
The Current Issue: Reports are purely textual.
The Upgrade:
Instruct the Writer agent to generate Mermaid.js diagrams (system architectures, timelines, or dataflows) directly in Markdown.
Extract numerical trends into structured JSON and render interactive Plotly charts inline in Streamlit.