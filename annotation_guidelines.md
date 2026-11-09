# Ground-Truth Dataset Annotation Protocol

This document defines the formal annotation procedure for the 45-question benchmark dataset used to evaluate retrieval strategies in the "Chat-with-your-Notes" study assistant.

## 1. Corpus Scope
The source corpus consists of academic lecture summaries and primary readings covering African American history:
- Mansa Musa and Medieval African Kingdoms
- The Transatlantic Slave Trade
- Antebellum Abolitionist Literature (e.g., David Walker)
- The Harlem Renaissance and the New Negro Movement
- The Modern Civil Rights Era

## 2. Question Formulation Criteria
- **Factual Lookup (20 Questions):** Direct entity, date, or event queries answered within a single chunk (e.g., author attribution, publication dates).
- **Comparative & Chronological Reasoning (10 Questions):** Queries requiring cross-passage synthesis across multiple pages (e.g., contrasting abolitionist philosophies).
- **Unanswerable / Out-of-Scope (15 Questions):** Queries on unrelated historical domains to evaluate hallucination prevention and negative rejection.

## 3. Ground-Truth Answer & Passage Bounding
- **Answer Form:** Reference answers must be concise, factual, and strictly limited to information present in the source PDF.
- **Supporting Context:** Annotators manually highlight the minimal span of text (chunk ID and PDF page number) necessary to verify the answer.
- **Rejection Standard:** For unanswerable queries, the ground-truth string is standardized to: *"I cannot answer this based on the provided notes."*, with an empty supporting context list (`[]`).