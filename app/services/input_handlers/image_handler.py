"""
Image input handler using Tesseract OCR.
Extracts text from images with confidence scoring.
"""

import base64
import io
from typing import Dict, Any

import pytesseract
from PIL import Image

from app.config import get_settings
from app.models.enums import HITLTriggerReason, InputMode
from app.models.schemas import ExtractionResult
from app.utils.logger import get_logger

logger = get_logger(__name__)


class ImageHandler:
    """Handles image input: decodes base64, runs Tesseract OCR, returns text + confidence."""

    def __init__(self):
        self._settings = get_settings()
        self._confidence_threshold = self._settings.ocr.get("confidence_threshold", 60)

    def extract(self, image_base64: str) -> ExtractionResult:
        """
        Extract text from a base64-encoded image using Tesseract OCR.

        Args:
            image_base64: Base64 encoded image string.

        Returns:
            ExtractionResult with text, confidence, and HITL flag.
        """
        try:
            # Decode the base64 image
            image_bytes = base64.b64decode(image_base64)
            image = Image.open(io.BytesIO(image_bytes))

            # Convert to RGB if needed (handles RGBA, grayscale, etc.)
            if image.mode != "RGB":
                image = image.convert("RGB")

            # Run OCR with detailed output for confidence scores
            ocr_data = pytesseract.image_to_data(
                image, output_type=pytesseract.Output.DICT
            )

            # Extract text and compute average confidence
            extracted_text, avg_confidence = self._process_ocr_data(ocr_data)

            # Also get plain text as fallback
            if not extracted_text.strip():
                extracted_text = pytesseract.image_to_string(image).strip()
                avg_confidence = 0.0  # No confidence info in plain mode

            # Determine if HITL is needed
            hitl_required = avg_confidence < self._confidence_threshold
            hitl_reason = (
                HITLTriggerReason.LOW_OCR_CONFIDENCE if hitl_required else None
            )

            logger.info(
                "ocr_extraction_complete",
                confidence=avg_confidence,
                text_length=len(extracted_text),
                hitl_required=hitl_required,
            )

            return ExtractionResult(
                extracted_text=extracted_text,
                confidence=avg_confidence / 100.0,  # Normalize to 0-1
                input_mode=InputMode.IMAGE,
                hitl_required=hitl_required,
                hitl_reason=hitl_reason,
                raw_details={
                    "engine": "tesseract",
                    "avg_confidence": avg_confidence,
                    "word_count": len(
                        [w for w in ocr_data.get("text", []) if w.strip()]
                    ),
                },
            )

        except Exception as e:
            logger.error("ocr_extraction_failed", error=str(e))
            return ExtractionResult(
                extracted_text="",
                confidence=0.0,
                input_mode=InputMode.IMAGE,
                hitl_required=True,
                hitl_reason=HITLTriggerReason.LOW_OCR_CONFIDENCE,
                raw_details={"error": str(e)},
            )

    def _process_ocr_data(self, ocr_data: Dict[str, Any]) -> tuple:
        """
        Process Tesseract detailed output to get clean text and avg confidence.

        Returns:
            Tuple of (extracted_text, average_confidence).
        """
        words = []
        confidences = []

        for i, text in enumerate(ocr_data.get("text", [])):
            conf = int(ocr_data["conf"][i])
            if conf > 0 and text.strip():  # Skip low-conf noise and empty strings
                words.append(text.strip())
                confidences.append(conf)

        extracted_text = " ".join(words)
        avg_confidence = (
            sum(confidences) / len(confidences) if confidences else 0.0
        )

        return extracted_text, avg_confidence
