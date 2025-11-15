"""
Pytest configuration and shared fixtures for tests.
"""
import os
import sys
from pathlib import Path
from unittest.mock import patch

# Add backend to path for imports
ROOT = Path(__file__).resolve().parents[1]
BACKEND_PATH = ROOT / "backend"
if str(BACKEND_PATH) not in sys.path:
    sys.path.insert(0, str(BACKEND_PATH))

# Set test environment variables
os.environ.setdefault("DB_HOST", "localhost")
os.environ.setdefault("DB_NAME", "RAG_Bot_test")
os.environ.setdefault("DB_USER", "postgres")
os.environ.setdefault("DB_PASSWORD", "postgres")
os.environ.setdefault("DB_PORT", "5432")
os.environ.setdefault("CHUNK_SIZE", "450")
os.environ.setdefault("CHUNK_OVERLAP", "75")
os.environ.setdefault("TEXT_EMBEDDING_MODEL", "BAAI/bge-large-en-v1.5")
os.environ.setdefault("IMAGE_EMBEDDING_MODEL", "laion/CLIP-ViT-H-14-laion2B-s32B-b79K")
os.environ.setdefault("TEXT_EMBEDDING_DIM", "1024")
os.environ.setdefault("IMAGE_EMBEDDING_DIM", "1024")
os.environ.setdefault("USE_PGVECTOR", "false")  # Disable pgvector for tests unless needed
os.environ.setdefault("TESTING", "true")  # Mark as testing environment - must be set before any app imports

