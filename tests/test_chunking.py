import sys
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND_PATH = ROOT / "backend"
if str(BACKEND_PATH) not in sys.path:
    sys.path.insert(0, str(BACKEND_PATH))

# Set TESTING flag before any imports
os.environ["TESTING"] = "true"

from app.services.pdf_processing import chunk_text  # noqa: E402


def test_chunk_text_overlap_preserved():
    text = " ".join(f"word{i}" for i in range(60))
    chunks = chunk_text(text, chunk_size=20, overlap=5)

    # With 60 words, chunk_size=20, overlap=5, step=15:
    # Chunk 1: words 0-19 (20 words)
    # Chunk 2: words 15-34 (20 words) - overlaps 5 words with chunk 1
    # Chunk 3: words 30-49 (20 words) - overlaps 5 words with chunk 2
    # Chunk 4: words 45-59 (15 words) - overlaps 5 words with chunk 3
    assert len(chunks) == 4

    # Verify overlap between consecutive chunks
    first_chunk_tokens = chunks[0].split()
    second_chunk_tokens = chunks[1].split()
    assert first_chunk_tokens[-5:] == second_chunk_tokens[:5], "First and second chunks should overlap by 5 words"

    second_chunk_tokens = chunks[1].split()
    third_chunk_tokens = chunks[2].split()
    assert second_chunk_tokens[-5:] == third_chunk_tokens[:5], "Second and third chunks should overlap by 5 words"

    third_chunk_tokens = chunks[2].split()
    fourth_chunk_tokens = chunks[3].split()
    assert third_chunk_tokens[-5:] == fourth_chunk_tokens[:5], "Third and fourth chunks should overlap by 5 words"


def test_chunk_text_handles_short_input():
    text = "short text"
    chunks = chunk_text(text, chunk_size=50, overlap=10)
    assert chunks == [text]

