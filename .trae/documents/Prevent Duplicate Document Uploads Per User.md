## Goal
Prevent duplicate uploads per user while offering a clear prompt to replace the existing document.

## Detection
- Compute a streaming SHA-256 `content_hash` for the uploaded PDF.
- Query existing `rag_documents` owned by the user with the same `content_hash`.
- If found, return 409 with the existing document’s metadata and a `can_replace: true` flag.

## Database
- Ensure `rag_documents` has `content_hash` and a unique index on `(owner_user_id, content_hash)` to enforce per-user uniqueness.

## Backend API
1. Upload flow (`POST /api/upload`)
   - On duplicate: return 409 payload `{ error, existing: { id, filename }, can_replace: true }`.
2. Replace flow (`POST /api/documents/{id}/replace`)
   - Auth required and ownership verified.
   - Accept multipart PDF. Recompute `content_hash`.
   - Update the existing record’s `filename`, `source_path`, `content_hash`, and `metadata`.
   - Option A: If the content differs, delete and re-ingest chunks for this document ID.
   - Option B: If the content hash matches, only update `filename`/`source_path` (fast path).

## Frontend UX
- On 409 from `/api/upload`, show a modal:
  - Message: “This document already exists as <filename>. Replace it?”
  - Buttons: `Replace` and `Cancel`.
  - Replace: sends the same file to `POST /api/documents/{existingId}/replace` with the auth token.
  - Cancel: dismisses modal; no upload occurs.
- Reuse existing status banners for success/error feedback.

## Edge Cases & Rules
- Only the owner can replace their document.
- Large PDFs: hashing uses streaming to avoid memory issues.
- If replace fails mid-run, return error and leave the original document intact.
- Keep `owner_user_id` unchanged on replace.

## Validation
- Unit tests: duplicate detection, replace endpoint success/failure, ownership checks.
- Manual: Upload same file twice under different names to trigger the prompt; verify both Replace and Cancel.

## Rollout
1. Add/verify DB index and `content_hash`.
2. Implement duplicate detection in upload and the replace endpoint.
3. Add the frontend modal handling and wire to the new endpoint.
4. Test end-to-end in dev.

Confirm this plan and I will implement the API changes, migration updates if needed, and the frontend prompt with minimal UI additions consistent with your design.