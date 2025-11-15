BEGIN;

ALTER TABLE rag_documents
  ADD COLUMN IF NOT EXISTS content_hash TEXT;

CREATE UNIQUE INDEX IF NOT EXISTS uniq_owner_content
  ON rag_documents(owner_user_id, content_hash);

COMMIT;