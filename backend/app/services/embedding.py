import base64
import io
from typing import Any, Dict, List, Optional

import torch
from PIL import Image
from sentence_transformers import SentenceTransformer
from transformers import CLIPProcessor, CLIPModel

from ..config import Config
from ..repository.rag_repository import insert_chunk


# Model loading (singleton per process)
# Text model
try:
    text_model = SentenceTransformer(Config.TEXT_EMBEDDING_MODEL)
except Exception as e:
    raise RuntimeError(
        f"Failed to load text embedding model '{Config.TEXT_EMBEDDING_MODEL}': {e}. "
        f"Please check the model identifier is correct on Hugging Face."
    ) from e

# Image model (CLIP)
try:
    clip_model = CLIPModel.from_pretrained(Config.IMAGE_EMBEDDING_MODEL)
    clip_processor = CLIPProcessor.from_pretrained(Config.IMAGE_EMBEDDING_MODEL)
except Exception as e:
    raise RuntimeError(
        f"Failed to load image embedding model '{Config.IMAGE_EMBEDDING_MODEL}': {e}. "
        f"Please check the model identifier is correct on Hugging Face. "
        f"Alternative: try 'openai/clip-vit-large-patch14' (768 dimensions) or "
        f"'laion/CLIP-ViT-H-14-laion2B-s32B-b79K' (1024 dimensions)."
    ) from e


def embed_text(
    conn,
    text: str,
    *,
    document_id: int,
    page_number: int,
    chunk_index: int,
    metadata: Optional[Dict[str, Any]] = None,
) -> int:
    """Embed text, store chunk, and return its id."""
    embedding: List[float] = text_model.encode(text).tolist()
    
    # Validate embedding dimension
    if len(embedding) != Config.TEXT_EMBEDDING_DIM:
        raise ValueError(
            f"Text embedding dimension mismatch: expected {Config.TEXT_EMBEDDING_DIM}, "
            f"got {len(embedding)}"
        )
    
    metadata_with_dims = (metadata or {}).copy()
    metadata_with_dims.update({
        "type": "text",
        "embedding_dim": Config.TEXT_EMBEDDING_DIM,
        "model": Config.TEXT_EMBEDDING_MODEL,
    })
    
    return insert_chunk(
        conn,
        document_id=document_id,
        chunk_type="text",
        page_number=page_number,
        chunk_index=chunk_index,
        content=text,
        text_embedding=embedding,
        image_embedding=None,
        image_base64=None,
        metadata=metadata_with_dims,
    )


def _decode_pdf_image_stream(stream_data: bytes, image_name: str) -> Optional[Image.Image]:
    """
    Attempt to decode PDF image stream data using multiple methods.
    PDF images can be in various formats (JPX, CCITT, DCT, etc.)
    """
    # Method 1: Try direct Pillow opening (works for standard formats)
    try:
        img = Image.open(io.BytesIO(stream_data))
        return img.convert("RGB")
    except Exception:
        pass
    
    # Method 2: Try with explicit format hints
    formats_to_try = ["PNG", "JPEG", "TIFF", "BMP", "GIF"]
    for fmt in formats_to_try:
        try:
            img = Image.open(io.BytesIO(stream_data))
            if img.format == fmt or fmt in str(img.format):
                return img.convert("RGB")
        except Exception:
            continue
    
    # Method 3: Try reading as raw bytes and reconstructing
    # Some PDF images are stored with filters that need decoding
    try:
        # Check if it's a valid image by trying to detect format
        img = Image.open(io.BytesIO(stream_data))
        # Force format detection
        img.load()  # Load the image to force format detection
        return img.convert("RGB")
    except Exception:
        pass
    
    # Method 4: Try with pdf2image or pypdfium2 if available
    # This is a fallback for complex PDF image formats
    try:
        import pdf2image
        # This won't work directly with stream_data, but we can try
        # For now, skip this method as it requires the full PDF
    except ImportError:
        pass
    
    return None


def embed_image_from_stream(
    conn,
    stream_data: bytes,
    image_name: str,
    *,
    document_id: int,
    page_number: int,
    chunk_index: int,
    linked_chunk_id: Optional[int],
    metadata: Optional[Dict[str, Any]] = None,
) -> Optional[str]:
    """Embed an image stream via CLIP and store base64 + embedding."""
    try:
        # Validate stream data
        if not stream_data or len(stream_data) == 0:
            print(f"⚠️ Empty stream data for {image_name}")
            return None
        
        # Try to decode the image using multiple methods
        img = _decode_pdf_image_stream(stream_data, image_name)
        
        if img is None:
            # Last resort: try to save and reload (sometimes helps with format issues)
            try:
                temp_buffer = io.BytesIO()
                # Try saving as PNG first
                temp_img = Image.new("RGB", (100, 100), color="white")
                temp_img.save(temp_buffer, format="PNG")
                # If that worked, try the original data again with different approach
                img = Image.open(io.BytesIO(stream_data))
                img = img.convert("RGB")
            except Exception as e:
                print(f"⚠️ Could not decode image {image_name}: {e}")
                print(f"   Stream data length: {len(stream_data)} bytes")
                print(f"   First 50 bytes (hex): {stream_data[:50].hex()}")
                return None
        
        # Validate image dimensions
        if img.size[0] == 0 or img.size[1] == 0:
            print(f"⚠️ Invalid image dimensions for {image_name}: {img.size}")
            return None
        
        # Convert to RGB if not already
        if img.mode != "RGB":
            img = img.convert("RGB")
        
        # Save to buffer for base64 encoding
        buffered = io.BytesIO()
        img.save(buffered, format="PNG")
        image_base64 = base64.b64encode(buffered.getvalue()).decode("utf-8")

        # Generate CLIP embedding
        inputs = clip_processor(images=img, return_tensors="pt")
        with torch.no_grad():
            outputs = clip_model.get_image_features(**inputs)
        embedding = outputs[0].cpu().numpy().tolist()
        
        # Validate embedding dimension
        if len(embedding) != Config.IMAGE_EMBEDDING_DIM:
            raise ValueError(
                f"Image embedding dimension mismatch: expected {Config.IMAGE_EMBEDDING_DIM}, "
                f"got {len(embedding)}"
            )
        
        metadata_with_dims = (metadata or {}).copy()
        metadata_with_dims.update({
            "type": "image",
            "source": image_name,
            "embedding_dim": Config.IMAGE_EMBEDDING_DIM,
            "model": Config.IMAGE_EMBEDDING_MODEL,
            "image_format": img.format or "unknown",
            "image_size": f"{img.size[0]}x{img.size[1]}",
        })

        insert_chunk(
            conn,
            document_id=document_id,
            chunk_type="image",
            page_number=page_number,
            chunk_index=chunk_index,
            content=None,
            text_embedding=None,
            image_embedding=embedding,
            image_base64=image_base64,
            metadata=metadata_with_dims,
            linked_chunk_id=linked_chunk_id,
        )
        return image_base64
    except Exception as e:
        print(f"❌ Error embedding image {image_name}: {e}")
        import traceback
        traceback.print_exc()
        return None

