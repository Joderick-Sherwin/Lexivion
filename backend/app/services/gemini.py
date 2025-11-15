import json
import logging
from typing import Any, Dict, List

try:
    import google.generativeai as genai
except ImportError:  # pragma: no cover - optional dependency
    genai = None

from ..config import Config

logger = logging.getLogger(__name__)


class GeminiClient:
    """Wrapper around Gemini to keep prompting logic centralized."""

    def __init__(self) -> None:
        self.enabled = bool(Config.GEMINI_API_KEY) and genai is not None
        self.model = None
        if not Config.GEMINI_API_KEY:
            logger.warning("GEMINI_API_KEY is not set. Gemini responses will be disabled.")
        if genai is None:
            logger.warning("google-generativeai package not installed. Gemini responses will be disabled.")
        if self.enabled:
            genai.configure(api_key=Config.GEMINI_API_KEY)
            self.model = genai.GenerativeModel(
                model_name=Config.GEMINI_MODEL,
                generation_config={
                    "temperature": 0.25,
                    "top_p": 0.9,
                    "top_k": 64,
                    "response_mime_type": Config.GEMINI_RESPONSE_MIME_TYPE,
                },
            )

    def _build_prompt(self, question: str, segments: List[Dict[str, Any]]) -> str:
        """Create structured text prompt for Gemini."""
        context_parts = []
        for seg in segments:
            chunk_info = f"[Chunk ID: {seg['chunk_id']}, Page: {seg.get('page_number', 'N/A')}]"
            content = seg.get("content", "").strip()
            if content:
                context_parts.append(f"{chunk_info}\n{content}")
        
        context_text = "\n\n---\n\n".join(context_parts)
        
        prompt = f"""You are an enterprise RAG assistant. Use only the provided context segments to answer the question.

Context segments:
{context_text}

Question: {question}

Instructions:
- Use only the information from the context segments above
- Return a JSON object with this exact structure:
{{
  "answer": "<overall response based on the context>",
  "sections": [
    {{
      "title": "<short heading for this section>",
      "chunk_ids": [<chunk_id_numbers_as_integers>],
      "text": "<detailed explanation using the referenced chunks>"
    }}
  ]
}}
- Only reference chunk_ids that appear in the context segments
- If information is missing, state that explicitly
- Ensure the JSON is valid and properly formatted"""
        
        return prompt

    def generate(self, question: str, segments: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Invoke Gemini and return parsed JSON response or fallback."""
        if not segments:
            return {
                "answer": "No relevant context was retrieved, so I cannot answer the question.",
                "sections": [],
                "source": "retriever",
            }

        if not self.enabled or self.model is None:
            logger.warning("Gemini client is disabled or model is None")
            return self._fallback_response(question, segments)

        prompt = self._build_prompt(question, segments)
        raw_text = ""
        try:
            logger.debug(f"Calling Gemini with prompt length: {len(prompt)}")
            response = self.model.generate_content(prompt)
            
            if not response:
                logger.error("Gemini returned empty response")
                return self._fallback_response(question, segments, error="Empty response from Gemini")
            
            # Extract text from response (handles different response structures)
            if hasattr(response, 'text') and response.text:
                raw_text = response.text
            elif hasattr(response, 'parts') and response.parts:
                # Try to get text from parts
                for part in response.parts:
                    if hasattr(part, 'text') and part.text:
                        raw_text = part.text
                        break
                    elif hasattr(part, 'text') and part.text is not None:
                        raw_text = str(part.text)
                        break
            else:
                raw_text = str(response)
            
            if not raw_text or not raw_text.strip():
                logger.error(f"Gemini response is empty. Response object: {type(response)}, has text: {hasattr(response, 'text')}, has parts: {hasattr(response, 'parts')}")
                return self._fallback_response(question, segments, error="Empty text in response")
            
            logger.debug(f"Gemini response length: {len(raw_text)}")
            
            # Try to extract JSON from response if it's wrapped in markdown code blocks
            if "```json" in raw_text:
                start = raw_text.find("```json") + 7
                end = raw_text.find("```", start)
                if end > start:
                    raw_text = raw_text[start:end].strip()
            elif "```" in raw_text:
                start = raw_text.find("```") + 3
                end = raw_text.find("```", start)
                if end > start:
                    raw_text = raw_text[start:end].strip()
            
            data = json.loads(raw_text)
            
            # Validate response structure
            if not isinstance(data, dict):
                logger.error(f"Gemini response is not a dict: {type(data)}")
                return self._fallback_response(question, segments, error="Invalid response format")
            
            # Ensure required fields exist
            if "answer" not in data:
                data["answer"] = ""
            if "sections" not in data:
                data["sections"] = []
            
            logger.info("Successfully generated Gemini response")
            return data
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Gemini JSON response: {e}")
            if raw_text:
                logger.error(f"Response text (first 500 chars): {raw_text[:500]}")
            return self._fallback_response(question, segments, error=f"JSON parse error: {str(e)}")
        except Exception as exc:
            logger.error(f"Gemini API call failed: {type(exc).__name__}: {exc}", exc_info=True)
            return self._fallback_response(question, segments, error=f"{type(exc).__name__}: {str(exc)}")

    @staticmethod
    def _fallback_response(question: str, segments: List[Dict[str, Any]], error: str = "") -> Dict[str, Any]:
        """Simple deterministic summary when Gemini is unavailable."""
        joined_context = "\n\n".join(seg["content"] for seg in segments if seg.get("content"))
        answer = (
            "Gemini was unavailable so this response is based on the retrieved context directly.\n\n"
            f"Question: {question}\n\nContext:\n{joined_context}"
        )
        if error:
            answer += f"\n\n[LLM Error: {error}]"
        return {
            "answer": answer,
            "sections": [
                {
                    "title": f"Context Segment {idx + 1}",
                    "chunk_ids": [str(seg["chunk_id"])],
                    "text": seg.get("content", ""),
                }
                for idx, seg in enumerate(segments)
            ],
            "source": "fallback",
        }


gemini_client = GeminiClient()

