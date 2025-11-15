-- Update vector column dimensions from 384 to 1024
-- This migration handles the upgrade from old 384-dim models to new 1024-dim models

-- Check if vector columns exist with wrong dimensions and update them
-- First, drop existing indexes if they exist
DROP INDEX IF EXISTS idx_rag_chunks_text_vector_hnsw;
DROP INDEX IF EXISTS idx_rag_chunks_image_vector_hnsw;
DROP INDEX IF EXISTS idx_rag_chunks_text_vector_ivfflat;

-- Drop existing vector columns if they have wrong dimensions
-- We'll recreate them with correct dimensions
ALTER TABLE rag_chunks DROP COLUMN IF EXISTS text_embedding_vector;
ALTER TABLE rag_chunks DROP COLUMN IF EXISTS image_embedding_vector;

-- Recreate vector columns with correct 1024 dimensions
ALTER TABLE rag_chunks
    ADD COLUMN text_embedding_vector vector(1024),
    ADD COLUMN image_embedding_vector vector(1024);

-- Recreate HNSW indexes for fast similarity search
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

-- Update backfill function to handle 1024 dimensions
CREATE OR REPLACE FUNCTION backfill_vector_embeddings()
RETURNS void AS $$
BEGIN
    -- Populate text embeddings (1024 dimensions)
    UPDATE rag_chunks
    SET text_embedding_vector = paired_text_embedding::vector
    WHERE paired_text_embedding IS NOT NULL 
      AND text_embedding_vector IS NULL
      AND jsonb_array_length(paired_text_embedding) = 1024;
    
    -- Populate image embeddings (1024 dimensions)
    UPDATE rag_chunks
    SET image_embedding_vector = embedding::vector
    WHERE embedding IS NOT NULL 
      AND image_embedding_vector IS NULL
      AND jsonb_array_length(embedding) = 1024;
END;
$$ LANGUAGE plpgsql;

