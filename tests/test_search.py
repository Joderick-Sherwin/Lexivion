"""
Tests for search service.
"""
import os
import pytest
from unittest.mock import Mock, patch, MagicMock

# Set TESTING flag before any imports
os.environ.setdefault("TESTING", "true")

from app.services.search import (
    search_rag_with_images,
    cosine_similarity,
    parse_embedding,
    _rank_chunks,
)


class TestCosineSimilarity:
    """Tests for cosine similarity calculation."""

    def test_cosine_similarity_identical_vectors(self):
        """Test that identical vectors have similarity of 1.0."""
        vec = [1.0, 2.0, 3.0]
        result = cosine_similarity(vec, vec)
        assert abs(result - 1.0) < 1e-6

    def test_cosine_similarity_orthogonal_vectors(self):
        """Test that orthogonal vectors have similarity of 0.0."""
        vec1 = [1.0, 0.0, 0.0]
        vec2 = [0.0, 1.0, 0.0]
        result = cosine_similarity(vec1, vec2)
        assert abs(result) < 1e-6

    def test_cosine_similarity_zero_vectors(self):
        """Test that zero vectors return 0.0."""
        vec1 = [0.0, 0.0, 0.0]
        vec2 = [1.0, 2.0, 3.0]
        result = cosine_similarity(vec1, vec2)
        assert result == 0.0

    def test_cosine_similarity_normalized(self):
        """Test that similarity is between -1 and 1."""
        vec1 = [1.0, 2.0, 3.0]
        vec2 = [4.0, 5.0, 6.0]
        result = cosine_similarity(vec1, vec2)
        assert -1.0 <= result <= 1.0


class TestParseEmbedding:
    """Tests for embedding parsing."""

    def test_parse_embedding_list(self):
        """Test parsing a list embedding."""
        emb = [1.0, 2.0, 3.0]
        result = parse_embedding(emb)
        assert result == emb

    def test_parse_embedding_string(self):
        """Test parsing a string representation of embedding."""
        emb = "[1.0, 2.0, 3.0]"
        result = parse_embedding(emb)
        assert result == [1.0, 2.0, 3.0]

    def test_parse_embedding_none(self):
        """Test parsing None returns None."""
        result = parse_embedding(None)
        assert result is None

    def test_parse_embedding_invalid_string(self):
        """Test parsing invalid string returns None."""
        result = parse_embedding("invalid")
        assert result is None


class TestSearchRAGWithImages:
    """Tests for RAG search with images."""

    @patch('app.services.search.text_model')
    @patch('app.services.search._rank_chunks')
    @patch('app.services.search.fetch_images_for_text_chunks')
    @patch('app.services.search.fetch_documents_by_ids')
    @patch('app.services.search.gemini_client')
    def test_search_rag_with_images_success(
        self, mock_gemini, mock_fetch_docs, mock_fetch_images,
        mock_rank_chunks, mock_text_model
    ):
        """Test successful RAG search."""
        # Setup
        mock_text_model.encode.return_value = [0.1] * 1024
        mock_rank_chunks.return_value = [
            {
                "id": 1,
                "document_id": 1,
                "page_number": 1,
                "chunk_index": 1,
                "content": "test content",
                "similarity": 0.9,
                "metadata": {},
            }
        ]
        mock_fetch_images.return_value = {1: []}
        mock_fetch_docs.return_value = {
            1: {"id": 1, "filename": "test.pdf", "source_path": "/path/to/test.pdf", "metadata": {}}
        }
        mock_gemini.generate.return_value = {
            "answer": "Test answer",
            "sections": [
                {
                    "title": "Test Section",
                    "chunk_ids": [1],
                    "text": "Test text",
                }
            ],
        }

        # Execute
        result = search_rag_with_images("test query", top_k=5)

        # Assert
        assert "answer" in result
        assert "sections" in result
        assert "context" in result
        assert result["query"] == "test query"
        assert result["top_k"] == 5

    @patch('app.services.search.text_model')
    @patch('app.services.search._rank_chunks')
    def test_search_rag_with_images_no_results(
        self, mock_rank_chunks, mock_text_model
    ):
        """Test RAG search with no results."""
        # Setup
        mock_text_model.encode.return_value = [0.1] * 1024
        mock_rank_chunks.return_value = []

        # Execute
        result = search_rag_with_images("test query", top_k=5)

        # Assert
        assert "answer" in result
        assert "sections" in result
        assert "context" in result
        assert len(result["context"]) == 0

