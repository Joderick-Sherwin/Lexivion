-- RAG pipeline upgrade: introduce documents metadata and richer chunk schema

CREATE TABLE IF NOT EXISTS rag_documents (
    id SERIAL PRIMARY KEY,
    filename TEXT NOT NULL,
    source_path TEXT,
    metadata JSONB,
    uploaded_at TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE rag_chunks
    ADD COLUMN IF NOT EXISTS document_id INTEGER REFERENCES rag_documents (id) ON DELETE CASCADE,
    ADD COLUMN IF NOT EXISTS chunk_type TEXT DEFAULT 'text',
    ADD COLUMN IF NOT EXISTS page_number INTEGER,
    ADD COLUMN IF NOT EXISTS chunk_index INTEGER,
    ADD COLUMN IF NOT EXISTS linked_chunk_id INTEGER,
    ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ DEFAULT NOW();

CREATE INDEX IF NOT EXISTS idx_rag_chunks_doc ON rag_chunks (document_id);
CREATE INDEX IF NOT EXISTS idx_rag_chunks_chunk_type ON rag_chunks (chunk_type);
CREATE INDEX IF NOT EXISTS idx_rag_chunks_linked ON rag_chunks (linked_chunk_id);

