import logging
import os
from contextlib import closing

from .config import Config
from .db import connect_db
from .services.gemini import gemini_client
from .services.embedding import text_model, clip_model

logger = logging.getLogger(__name__)


def _is_ci_environment() -> bool:
    ci_indicators = [
        "CI",
        "GITHUB_ACTIONS",
        "TRAVIS",
        "JENKINS_URL",
        "GITLAB_CI",
        "CIRCLECI",
        "APPVEYOR",
        "TEAMCITY_VERSION",
    ]
    return any(os.getenv(indicator) for indicator in ci_indicators)


def _check_database() -> bool:
    """Verify database connectivity."""
    try:
        with closing(connect_db()) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1;")
        logger.info(
            "Database connection successful (host=%s db=%s user=%s)",
            Config.DB_HOST,
            Config.DB_NAME,
            Config.DB_USER,
        )
        return True
    except Exception as exc:
        logger.exception("Database connection failed: %s", exc)
        return False


def _check_gemini() -> bool:
    """Ensure Gemini API key is configured and client is enabled."""
    if not Config.GEMINI_API_KEY:
        logger.error("GEMINI_API_KEY / GOOGLE_API_KEY is not set.")
        return False

    if not gemini_client.enabled or gemini_client.model is None:
        logger.error("Gemini client is disabled even though API key is set.")
        return False

    logger.info(
        "Gemini client ready (model=%s, response_mime_type=%s)",
        Config.GEMINI_MODEL,
        Config.GEMINI_RESPONSE_MIME_TYPE,
    )
    return True


def _check_embedding_models() -> bool:
    """Verify embedding models load correctly and return expected dimensions."""
    try:
        # Test text model
        test_text = "Test embedding"
        text_embedding = text_model.encode(test_text).tolist()
        if len(text_embedding) != Config.TEXT_EMBEDDING_DIM:
            logger.error(
                f"Text embedding dimension mismatch: expected {Config.TEXT_EMBEDDING_DIM}, "
                f"got {len(text_embedding)}"
            )
            return False
        
        logger.info(
            f"Text embedding model ready: {Config.TEXT_EMBEDDING_MODEL} "
            f"({Config.TEXT_EMBEDDING_DIM} dimensions)"
        )
        
        # Test image model (check if it loads, full test requires an image)
        if clip_model is None:
            logger.error("Image embedding model failed to load")
            return False
        
        logger.info(
            f"Image embedding model ready: {Config.IMAGE_EMBEDDING_MODEL} "
            f"({Config.IMAGE_EMBEDDING_DIM} dimensions)"
        )
        
        return True
    except Exception as exc:
        logger.exception(f"Embedding model check failed: {exc}")
        return False


def _check_pgvector() -> bool:
    """Check if pgvector extension is available (if enabled)."""
    if not Config.USE_PGVECTOR:
        logger.info("pgvector is disabled, skipping check")
        return True
    
    try:
        with closing(connect_db()) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM pg_extension WHERE extname = 'vector';")
                result = cur.fetchone()
                if result is None:
                    logger.warning(
                        "pgvector extension not found in database. "
                        "Run migration 003_high_dim_embeddings.sql to install it."
                    )
                    return False
        logger.info("pgvector extension is available")
        return True
    except Exception as exc:
        logger.warning(f"pgvector check failed (may not be installed): {exc}")
        return False


def run_startup_checks() -> None:
    """
    Run mandatory startup checks before the server begins serving requests.
    Raises RuntimeError if any critical dependency is unavailable.
    
    Automatically skips checks in CI environments where dependencies may not be available.
    """
    if os.getenv("SKIP_STARTUP_CHECKS") in ("1", "true", "True"):
        logger.info("Startup checks skipped by configuration.")
        return
    
    # Skip startup checks in CI environments
    if _is_ci_environment():
        logger.info("CI environment detected. Skipping startup checks.")
        return
    
    # Skip startup checks if TESTING environment variable is set
    if os.getenv("TESTING") == "true":
        logger.info("Testing environment detected. Skipping startup checks.")
        return
    
    logger.info("Running startup checks...")
    checks = {
        "database": _check_database(),
        "gemini": _check_gemini(),
        "embedding_models": _check_embedding_models(),
    }
    
    # pgvector check is non-critical (falls back to JSONB)
    pgvector_ok = _check_pgvector()
    if not pgvector_ok:
        logger.warning(
            "pgvector not available. Vector search will fall back to JSONB. "
            "Performance may be degraded for large datasets."
        )

    failed = [name for name, ok in checks.items() if not ok]
    if failed:
        raise RuntimeError(f"Startup checks failed: {', '.join(failed)}")

    logger.info("All startup checks passed successfully.")

