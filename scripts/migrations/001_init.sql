-- Initial schema for rag_chunks using JSONB for embeddings and metadata
CREATE TABLE IF NOT EXISTS rag_chunks (
    id SERIAL PRIMARY KEY,
    content TEXT NULL,
    paired_text_embedding JSONB NULL,
    embedding JSONB NULL,
    image_base64 TEXT NULL,
    metadata JSONB NULL
);

CREATE INDEX IF NOT EXISTS idx_rag_chunks_metadata ON rag_chunks USING GIN (metadata);

