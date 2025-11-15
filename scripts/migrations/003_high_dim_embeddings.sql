-- High-dimensional embeddings upgrade: Add pgvector support and vector columns
-- This migration adds vector columns for efficient similarity search with 1024+ dimensions

-- Install pgvector extension (requires superuser privileges)
CREATE EXTENSION IF NOT EXISTS vector;

-- Drop existing vector columns if they exist (they might have wrong dimensions)
-- This handles the upgrade from 384-dim to 1024-dim models
DROP INDEX IF EXISTS idx_rag_chunks_text_vector_hnsw;
DROP INDEX IF EXISTS idx_rag_chunks_image_vector_hnsw;
DROP INDEX IF EXISTS idx_rag_chunks_text_vector_ivfflat;
ALTER TABLE rag_chunks DROP COLUMN IF EXISTS text_embedding_vector;
ALTER TABLE rag_chunks DROP COLUMN IF EXISTS image_embedding_vector;

-- Add vector columns for text and image embeddings with correct 1024 dimensions
ALTER TABLE rag_chunks
    ADD COLUMN text_embedding_vector vector(1024),
    ADD COLUMN image_embedding_vector vector(1024);

-- Create HNSW indexes for fast similarity search
-- HNSW (Hierarchical Navigable Small World) provides O(log n) search performance
CREATE INDEX IF NOT EXISTS idx_rag_chunks_text_vector_hnsw 
    ON rag_chunks 
    USING hnsw (text_embedding_vector vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);

CREATE INDEX IF NOT EXISTS idx_rag_chunks_image_vector_hnsw 
    ON rag_chunks 
    USING hnsw (image_embedding_vector vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);

-- Create additional indexes for common queries
CREATE INDEX IF NOT EXISTS idx_rag_chunks_text_vector_ivfflat 
    ON rag_chunks 
    USING ivfflat (text_embedding_vector vector_cosine_ops)
    WITH (lists = 100);

-- Note: IVFFlat is faster to build but HNSW is generally better for accuracy
-- Both indexes are created for flexibility

-- Function to populate vector columns from JSONB embeddings (for existing data)
-- This can be run manually after migration to backfill existing embeddings
CREATE OR REPLACE FUNCTION backfill_vector_embeddings()
RETURNS void AS $$
BEGIN
    -- Populate text embeddings
    UPDATE rag_chunks
    SET text_embedding_vector = paired_text_embedding::vector
    WHERE paired_text_embedding IS NOT NULL 
      AND text_embedding_vector IS NULL
      AND jsonb_array_length(paired_text_embedding) = 1024;
    
    -- Populate image embeddings
    UPDATE rag_chunks
    SET image_embedding_vector = embedding::vector
    WHERE embedding IS NOT NULL 
      AND image_embedding_vector IS NULL
      AND jsonb_array_length(embedding) = 1024;
END;
$$ LANGUAGE plpgsql;

-- Add comment for documentation
COMMENT ON COLUMN rag_chunks.text_embedding_vector IS 'Vector embedding for text (1024 dimensions) using pgvector';
COMMENT ON COLUMN rag_chunks.image_embedding_vector IS 'Vector embedding for images (1024 dimensions) using pgvector';

