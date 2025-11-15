## Goal
Implement near‑duplicate handling so small edits to a PDF don’t block upload, but users are warned and can choose to replace. Keep exact byte‑level deduplication as is.

## Approach Overview
1. Keep existing exact dedupe via `content_hash` (raw bytes, SHA‑256).
2. Add soft checks:
   - Normalized text hash (dedupe despite minor PDF changes).
   - Optional semantic similarity using `pgvector`.
3. Return informative `409` responses with candidates and allow user‑initiated replace.

## Phase 1: Normalized Text Hash (Soft Check)
1. Schema
   - Add `rag_documents.content_hash_normalized TEXT`.
   - Add non‑unique index: `CREATE INDEX IF NOT EXISTS idx_docs_owner_normhash ON rag_documents(owner_user_id, content_hash_normalized);`
2. Backend – Hashing
   - In `backend/app/routes/ingest.py` after saving the file, extract text quickly (e.g., `pdfplumber`), normalize, and compute SHA‑256:
     - Normalization: lowercase, collapse whitespace (`\s+` → single space), strip leading/trailing spaces.
     - `norm_hash = sha256(normalized_text.encode('utf-8')).hexdigest()`.
   - Do the same in `backend/app/routes/documents.py::replace_document`.
3. Repository
   - Add `fetch_document_by_normalized_hash(owner_user_id, norm_hash)` in `rag_repository.py`.
   - Update `insert_document` and `update_document_metadata` to store `content_hash_normalized`.
4. Upload Flow
   - Order: check raw `content_hash` (exact dedupe) → check `content_hash_normalized` (soft dedupe) → proceed.
   - On normalized match, return `409` with payload:
     - `{ type: "normalized_match", existing_document_id, existing_filename, can_replace: true, similarity_hint: "normalized" }`.
   - Frontend shows a prompt to replace or continue as new (continue requires explicit override).
5. Replace Flow
   - Recompute normalized hash; update document record; purge old chunks and re‑ingest as implemented.

## Phase 2: Semantic Similarity (Optional, Stronger Soft Check)
1. Schema
   - Add `rag_documents.doc_embedding_vector vector(1024)` (match `Config.TEXT_EMBEDDING_DIM`).
   - Add pgvector index: `CREATE INDEX IF NOT EXISTS idx_docs_owner_docvec ON rag_documents USING hnsw (doc_embedding_vector) WITH (m=16, ef_construction=200);`
2. Backend – Embedding
   - Compute a document‑level embedding:
     - Fast: encode concatenation of first N pages’ text with `text_model.encode`.
     - Or: average of text‑chunk embeddings produced in `pdf_processing`.
   - Store in `rag_documents.doc_embedding_vector`.
3. Repository
   - Add `fetch_similar_documents(owner_user_id, query_vector, top_k)` with cosine similarity (`1 - <=>`).
4. Upload Flow
   - After raw/normalized checks, compute a provisional embedding (first N pages) and query top‑k.
   - If top hit similarity ≥ `Config.SEMANTIC_DUP_THRESHOLD` (e.g., 0.92), return `409` with `{ type: "semantic_match", candidates: [{id, filename, similarity}, ...], can_replace: true }`.
   - Frontend lets user replace or upload anyway.
5. Replace Flow
   - Update `doc_embedding_vector` alongside re‑ingestion.

## Frontend Changes
1. Handle `409` with `type` field:
   - `normalized_match`: show “Looks like an existing document with minor changes.”
   - `semantic_match`: list candidates with similarity scores.
2. Offer actions:
   - Replace existing (`POST /api/documents/<id>/replace`).
   - Upload anyway (`POST /api/upload?override=true`) — backend should accept when explicitly overridden.

## Config & Thresholds
- Add flags: `NORM_HASH_ENABLED`, `SEMANTIC_DUP_ENABLED`.
- Thresholds: `SEMANTIC_DUP_THRESHOLD` (default 0.92), `SEMANTIC_DUP_TOPK` (default 5), `NORM_HASH_MAX_PAGES` to cap normalization cost.

## Observability
- Log dedupe decisions with `owner_user_id`, hash type, and candidate IDs.
- Add metrics counters for exact/normalized/semantic matches.

## Rollout Strategy
1. Ship Phase 1 behind `NORM_HASH_ENABLED=true`.
2. Backfill `content_hash_normalized` for existing documents by reading stored files where available.
3. Phase 2 behind `SEMANTIC_DUP_ENABLED=false` initially; backfill `doc_embedding_vector` using existing text chunks.
4. Gradually enable semantic checks and monitor false positives.

## Files to Touch
- `scripts/migrations/007_normalized_hash.sql` (new migration).
- `backend/app/routes/ingest.py` and `backend/app/routes/documents.py` (hash computation + flow).
- `backend/app/services/pdf_processing.py` (optional: doc embedding aggregation).
- `backend/app/repository/rag_repository.py` (lookup by normalized hash; doc‑vector search; insert/update fields).
- `backend/app/config.py` (flags + thresholds).
- Frontend: upload handler and replace modal.

## Validation
- Unit tests for normalization function and hash stability.
- Integration tests: upload exact duplicate → 409 (exact); minor edit → 409 (normalized); different doc → 200.
- Semantic test: upload near‑duplicate → 409 with candidate list when threshold met.

Confirm this plan and I’ll implement Phase 1 first, then add Phase 2 behind a feature flag.