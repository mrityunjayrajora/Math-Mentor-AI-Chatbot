"""
Text input handler - passthrough with basic sanitization.
"""

from app.models.enums import InputMode
from app.models.schemas import ExtractionResult
from app.utils.logger import get_logger

logger = get_logger(__name__)


class TextHandler:
    """Handles plain text input with basic sanitization."""

    def extract(self, text: str) -> ExtractionResult:
        """
        Process text input with basic sanitization.

        Args:
            text: Raw text input from the user.

        Returns:
            ExtractionResult with cleaned text and full confidence.
        """
        # Basic sanitization
        cleaned = text.strip()

        # Remove null bytes and control characters (except newlines and tabs)
        cleaned = "".join(
            ch for ch in cleaned
            if ch == "\n" or ch == "\t" or (ord(ch) >= 32)
        )

        logger.info("text_extraction_complete", text_length=len(cleaned))

        return ExtractionResult(
            extracted_text=cleaned,
            confidence=1.0,
            input_mode=InputMode.TEXT,
            hitl_required=False,
            hitl_reason=None,
            raw_details={"engine": "text_passthrough"},
        )
