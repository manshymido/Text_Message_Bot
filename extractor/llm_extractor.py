"""LLM-based extraction for complex natural language using Google Gemini."""

import json
from typing import Optional

import google.generativeai as genai

from extractor.models import EventType, SchoolEvent
from utils.config import settings
from utils.logger import logger

# System prompt for structured extraction
EXTRACTION_PROMPT = """You are an AI assistant that extracts school-related information from text messages.

Extract the following information if present:
- Title: What is the event/assignment/exam about?
- Type: assignment, exam, class, meeting, or other
- Date: When does it occur? (ISO format)
- Due Date: When is it due? (for assignments, ISO format)
- Description: Any additional details
- Location: Where does it occur? (if mentioned)

Return ONLY a valid JSON object with this structure (no markdown, no code blocks):
{
  "title": "string",
  "event_type": "assignment|exam|class|meeting|other",
  "date": "YYYY-MM-DDTHH:MM:SS or null",
  "due_date": "YYYY-MM-DDTHH:MM:SS or null",
  "description": "string or null",
  "location": "string or null",
  "confidence": 0.0-1.0
}

If information is not clear or not present, use null. Only extract if the text is clearly school-related. Return only the JSON object, nothing else."""


class LLMExtractor:
    """Extract school-related information using Google Gemini."""

    def __init__(self):
        """Initialize LLM extractor with Gemini."""
        if not settings.gemini_api_key:
            logger.warning("Gemini API key not set. LLM extraction disabled.")
            self.model = None
        else:
            try:
                genai.configure(api_key=settings.gemini_api_key)
                self.model = genai.GenerativeModel("gemini-2.5-flash")
                logger.info("Gemini LLM extractor initialized")
            except Exception as e:
                logger.error(f"Failed to initialize Gemini client: {e}")
                self.model = None

    def extract(self, text: str) -> Optional[SchoolEvent]:
        """
        Extract school event information using Gemini.

        Args:
            text: Input text to extract from

        Returns:
            SchoolEvent if extraction successful, None otherwise
        """
        if not self.model or not settings.enable_llm_extraction:
            return None

        if not text or len(text.strip()) < 10:
            return None

        try:
            # Prepare the prompt
            full_prompt = f"{EXTRACTION_PROMPT}\n\nMessage to extract from:\n{text}"

            # Generate response using Gemini
            response = self.model.generate_content(
                full_prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.3,
                    top_p=0.95,
                    top_k=40,
                ),
            )

            content = response.text.strip()
            if not content:
                return None

            # Clean up response (remove markdown code blocks if present)
            if content.startswith("```json"):
                content = content[7:]
            if content.startswith("```"):
                content = content[3:]
            if content.endswith("```"):
                content = content[:-3]
            content = content.strip()

            data = json.loads(content)

            # Validate and create SchoolEvent
            if not data.get("title") or data.get("confidence", 0) < 0.3:
                return None

            # Parse dates
            from dateparser import parse as parse_date

            date = None
            if data.get("date"):
                date = parse_date(data["date"])

            due_date = None
            if data.get("due_date"):
                due_date = parse_date(data["due_date"])

            # Normalize event type
            event_type_str = data.get("event_type", "other").lower()
            event_type = EventType.OTHER
            for et in EventType:
                if et.value == event_type_str:
                    event_type = et
                    break

            return SchoolEvent(
                title=data.get("title", "Untitled"),
                event_type=event_type,
                date=date,
                due_date=due_date,
                description=data.get("description"),
                location=data.get("location"),
                confidence=data.get("confidence", 0.5),
                source_text=text,
            )

        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse LLM response as JSON: {e}")
            return None
        except Exception as e:
            logger.error(f"LLM extraction failed: {e}")
            return None

