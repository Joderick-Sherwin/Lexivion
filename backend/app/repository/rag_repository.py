from typing import Any, Dict, Iterable, List, Optional, Sequence

from psycopg2.extras import Json

from ..config import Config
from ..db import connect_db


def insert_document(conn, filename: str, source_path: str, metadata: Optional[Dict[str, Any]] = None) -> int:
    """Create a document record and return its id."""
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO rag_documents (filename, source_path, metadata)
                VALUES (%s, %s, %s)
                RETURNING id;
                """,
                (filename, source_path, Json(metadata or {})),
            )
            document_id = cur.fetchone()[0]
        conn.commit()
        return document_id
    except Exception as exc:
        conn.rollback()
        raise RuntimeError(f"Failed to insert document metadata: {exc}") from exc


def insert_chunk(
    conn,
    *,
    document_id: int,
    chunk_type: str,
    page_number: Optional[int],
    chunk_index: Optional[int],
    content: Optional[str],
    text_embedding: Optional[List[float]],
    image_embedding: Optional[List[float]],
    image_base64: Optional[str],
    metadata: Dict[str, Any],
    linked_chunk_id: Optional[int] = None,
) -> int:
    """Insert a chunk row into rag_chunks and return the id."""
    try:
        with conn.cursor() as cur:
            # Convert embeddings to vector format if pgvector is enabled
            text_vector = None
            image_vector = None
            
            if Config.USE_PGVECTOR:
                if text_embedding is not None:
                    # Convert list to vector string format: '[1.0,2.0,3.0]'
                    text_vector = "[" + ",".join(str(f) for f in text_embedding) + "]"
                if image_embedding is not None:
                    image_vector = "[" + ",".join(str(f) for f in image_embedding) + "]"
            
            # Build SQL with conditional vector columns
            if Config.USE_PGVECTOR:
                cur.execute(
                    """
                    INSERT INTO rag_chunks (
                        document_id,
                        chunk_type,
                        page_number,
                        chunk_index,
                        content,
                        paired_text_embedding,
                        embedding,
                        text_embedding_vector,
                        image_embedding_vector,
                        image_base64,
                        metadata,
                        linked_chunk_id
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s::vector, %s::vector, %s, %s, %s)
                    RETURNING id;
                    """,
                    (
                        document_id,
                        chunk_type,
                        page_number,
                        chunk_index,
                        content,
                        Json(text_embedding) if text_embedding is not None else None,
                        Json(image_embedding) if image_embedding is not None else None,
                        text_vector,
                        image_vector,
                        image_base64,
                        Json(metadata),
                        linked_chunk_id,
                    ),
                )
            else:
                cur.execute(
                    """
                    INSERT INTO rag_chunks (
                        document_id,
                        chunk_type,
                        page_number,
                        chunk_index,
                        content,
                        paired_text_embedding,
                        embedding,
                        image_base64,
                        metadata,
                        linked_chunk_id
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id;
                    """,
                    (
                        document_id,
                        chunk_type,
                        page_number,
                        chunk_index,
                        content,
                        Json(text_embedding) if text_embedding is not None else None,
                        Json(image_embedding) if image_embedding is not None else None,
                        image_base64,
                        Json(metadata),
                        linked_chunk_id,
                    ),
                )
            chunk_id = cur.fetchone()[0]
        conn.commit()
        return chunk_id
    except Exception as exc:
        conn.rollback()
        raise RuntimeError(f"Failed to insert chunk: {exc}") from exc


def fetch_text_chunks(limit: Optional[int] = None) -> List[Dict[str, Any]]:
    """Fetch text chunks ordered by recency."""
    conn = connect_db()
    try:
        limit_clause = "LIMIT %s" if limit else ""
        params: Sequence[Any] = (limit,) if limit else ()
        with conn.cursor() as cur:
            cur.execute(
                f"""
                SELECT
                    id,
                    document_id,
                    page_number,
                    chunk_index,
                    content,
                    paired_text_embedding,
                    metadata
                FROM rag_chunks
                WHERE chunk_type = 'text' AND paired_text_embedding IS NOT NULL
                ORDER BY created_at DESC
                {limit_clause};
                """,
                params,
            )
            rows = cur.fetchall()
        chunks: List[Dict[str, Any]] = []
        for row in rows:
            (
                chunk_id,
                document_id,
                page_number,
                chunk_index,
                content,
                embedding,
                metadata,
            ) = row
            chunks.append(
                {
                    "id": chunk_id,
                    "document_id": document_id,
                    "page_number": page_number,
                    "chunk_index": chunk_index,
                    "content": content,
                    "paired_text_embedding": embedding,
                    "metadata": metadata or {},
                }
            )
        return chunks
    finally:
        conn.close()


def fetch_images_for_text_chunks(parent_chunk_ids: Sequence[int]) -> Dict[int, List[Dict[str, Any]]]:
    """Return images keyed by their linked text chunk id."""
    if not parent_chunk_ids:
        return {}

    conn = connect_db()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    id,
                    linked_chunk_id,
                    page_number,
                    chunk_index,
                    image_base64,
                    metadata
                FROM rag_chunks
                WHERE chunk_type = 'image'
                  AND linked_chunk_id = ANY(%s)
                """,
                (list(parent_chunk_ids),),
            )
            rows = cur.fetchall()
        grouped: Dict[int, List[Dict[str, Any]]] = {}
        for row in rows:
            (
                chunk_id,
                linked_chunk_id,
                page_number,
                chunk_index,
                image_b64,
                metadata,
            ) = row
            grouped.setdefault(linked_chunk_id, []).append(
                {
                    "id": chunk_id,
                    "linked_chunk_id": linked_chunk_id,
                    "page_number": page_number,
                    "chunk_index": chunk_index,
                    "image_base64": image_b64,
                    "metadata": metadata or {},
                }
            )
        return grouped
    finally:
        conn.close()


def fetch_chunks_by_ids(chunk_ids: Iterable[int]) -> List[Dict[str, Any]]:
    if not chunk_ids:
        return []

    conn = connect_db()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    id,
                    document_id,
                    chunk_type,
                    page_number,
                    chunk_index,
                    content,
                    metadata
                FROM rag_chunks
                WHERE id = ANY(%s)
                """,
                (list(chunk_ids),),
            )
            rows = cur.fetchall()
        results: List[Dict[str, Any]] = []
        for row in rows:
            (
                chunk_id,
                document_id,
                chunk_type,
                page_number,
                chunk_index,
                content,
                metadata,
            ) = row
            results.append(
                {
                    "id": chunk_id,
                    "document_id": document_id,
                    "chunk_type": chunk_type,
                    "page_number": page_number,
                    "chunk_index": chunk_index,
                    "content": content,
                    "metadata": metadata or {},
                }
            )
        return results
    finally:
        conn.close()


def fetch_documents_by_ids(document_ids: Iterable[int]) -> Dict[int, Dict[str, Any]]:
    doc_ids = list({doc_id for doc_id in document_ids if doc_id})
    if not doc_ids:
        return {}

    conn = connect_db()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, filename, source_path, metadata
                FROM rag_documents
                WHERE id = ANY(%s)
                """,
                (doc_ids,),
            )
            rows = cur.fetchall()
        return {
            row[0]: {
                "id": row[0],
                "filename": row[1],
                "source_path": row[2],
                "metadata": row[3] or {},
            }
            for row in rows
        }
    finally:
        conn.close()


def fetch_document_by_id(document_id: int) -> Optional[Dict[str, Any]]:
    documents = fetch_documents_by_ids([document_id])
    return documents.get(document_id)


def fetch_text_chunks_with_vector_search(
    query_embedding: List[float], top_k: int
) -> List[Dict[str, Any]]:
    """Fetch top-k text chunks using pgvector cosine similarity search."""
    if not Config.USE_PGVECTOR:
        raise RuntimeError("pgvector is not enabled")
    
    conn = connect_db()
    try:
        # Convert query embedding to vector string format
        query_vector = "[" + ",".join(str(f) for f in query_embedding) + "]"
        
        with conn.cursor() as cur:
            # Use pgvector cosine distance operator (<=>) for similarity search
            # Lower distance = higher similarity, so we order by distance ASC
            cur.execute(
                """
                SELECT
                    id,
                    document_id,
                    page_number,
                    chunk_index,
                    content,
                    paired_text_embedding,
                    metadata,
                    1 - (text_embedding_vector <=> %s::vector) as similarity
                FROM rag_chunks
                WHERE chunk_type = 'text' 
                  AND text_embedding_vector IS NOT NULL
                ORDER BY text_embedding_vector <=> %s::vector
                LIMIT %s;
                """,
                (query_vector, query_vector, top_k),
            )
            rows = cur.fetchall()
        
        chunks: List[Dict[str, Any]] = []
        for row in rows:
            (
                chunk_id,
                document_id,
                page_number,
                chunk_index,
                content,
                embedding,
                metadata,
                similarity,
            ) = row
            chunks.append(
                {
                    "id": chunk_id,
                    "document_id": document_id,
                    "page_number": page_number,
                    "chunk_index": chunk_index,
                    "content": content,
                    "paired_text_embedding": embedding,
                    "metadata": metadata or {},
                    "similarity": float(similarity) if similarity is not None else 0.0,
                }
            )
        return chunks
    finally:
        conn.close()

