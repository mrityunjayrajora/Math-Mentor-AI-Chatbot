"""
Audio input handler using OpenAI Whisper.
Converts speech to text with math-specific post-processing.
"""

import base64
import os
import tempfile
from typing import Optional

import whisper

from app.config import get_settings
from app.models.enums import HITLTriggerReason, InputMode
from app.models.schemas import ExtractionResult
from app.utils.logger import get_logger

logger = get_logger(__name__)

# Math-specific phrase replacements for post-processing
MATH_PHRASE_MAP = {
    "square root of": "√",
    "square root": "√",
    "cube root of": "∛",
    "cube root": "∛",
    "raised to the power of": "^",
    "raised to the power": "^",
    "raised to": "^",
    "to the power of": "^",
    "to the power": "^",
    "squared": "^2",
    "cubed": "^3",
    "divided by": "/",
    "multiplied by": "*",
    "times": "*",
    "plus": "+",
    "minus": "-",
    "equals": "=",
    "is equal to": "=",
    "greater than or equal to": ">=",
    "less than or equal to": "<=",
    "greater than": ">",
    "less than": "<",
    "not equal to": "!=",
    "pi": "π",
    "theta": "θ",
    "alpha": "α",
    "beta": "β",
    "gamma": "γ",
    "delta": "δ",
    "sigma": "σ",
    "lambda": "λ",
    "infinity": "∞",
    "integral of": "∫",
    "summation of": "∑",
    "derivative of": "d/dx",
    "partial derivative": "∂",
    "limit as": "lim",
    "approaches": "→",
    "factorial": "!",
    "modulo": "%",
    "absolute value of": "|",
    "log base": "log_",
    "natural log": "ln",
    "natural logarithm": "ln",
}


class AudioHandler:
    """Handles audio input: decodes base64, runs Whisper ASR, post-processes math."""

    def __init__(self):
        self._settings = get_settings()
        self._model_size = self._settings.asr.get("model_size", "base")
        self._confidence_threshold = self._settings.asr.get(
            "confidence_threshold", 0.7
        )
        self._model: Optional[whisper.Whisper] = None

    def _load_model(self):
        """Lazy-load the Whisper model."""
        if self._model is None:
            logger.info("loading_whisper_model", model_size=self._model_size)
            self._model = whisper.load_model(self._model_size)
            logger.info("whisper_model_loaded")

    def extract(self, audio_base64: str, audio_format: str = "wav") -> ExtractionResult:
        """
        Extract text from base64-encoded audio using Whisper.

        Args:
            audio_base64: Base64 encoded audio data.
            audio_format: Audio format (wav, mp3, etc.).

        Returns:
            ExtractionResult with transcript, confidence, and HITL flag.
        """
        try:
            self._load_model()

            # Decode base64 to temp file
            audio_bytes = base64.b64decode(audio_base64)

            with tempfile.NamedTemporaryFile(
                suffix=f".{audio_format}", delete=False
            ) as tmp_file:
                tmp_file.write(audio_bytes)
                tmp_path = tmp_file.name

            try:
                # Run Whisper transcription
                result = self._model.transcribe(
                    tmp_path,
                    language="en",
                    fp16=False,  # CPU-safe
                )

                raw_text = result.get("text", "").strip()

                # Compute confidence from segment-level log probabilities
                confidence = self._compute_confidence(result)

                # Post-process for math-specific phrases
                processed_text = self._post_process_math(raw_text)

                # Determine if HITL is needed
                hitl_required = confidence < self._confidence_threshold
                hitl_reason = (
                    HITLTriggerReason.LOW_ASR_CONFIDENCE if hitl_required else None
                )

                logger.info(
                    "asr_transcription_complete",
                    confidence=confidence,
                    raw_length=len(raw_text),
                    processed_length=len(processed_text),
                    hitl_required=hitl_required,
                )

                return ExtractionResult(
                    extracted_text=processed_text,
                    confidence=confidence,
                    input_mode=InputMode.AUDIO,
                    hitl_required=hitl_required,
                    hitl_reason=hitl_reason,
                    raw_details={
                        "engine": "whisper",
                        "model_size": self._model_size,
                        "raw_text": raw_text,
                        "language": result.get("language", "en"),
                    },
                )

            finally:
                # Clean up temp file
                os.unlink(tmp_path)

        except Exception as e:
            logger.error("asr_transcription_failed", error=str(e))
            return ExtractionResult(
                extracted_text="",
                confidence=0.0,
                input_mode=InputMode.AUDIO,
                hitl_required=True,
                hitl_reason=HITLTriggerReason.LOW_ASR_CONFIDENCE,
                raw_details={"error": str(e)},
            )

    def _compute_confidence(self, result: dict) -> float:
        """
        Compute overall confidence from Whisper segment-level data.
        Uses average of no_speech_prob inverse as a proxy.
        """
        segments = result.get("segments", [])
        if not segments:
            return 0.0

        # Use avg_logprob as confidence proxy (higher = more confident)
        # Typical range: -1.0 (low) to 0.0 (high)
        avg_logprobs = [
            seg.get("avg_logprob", -1.0) for seg in segments
        ]
        no_speech_probs = [
            seg.get("no_speech_prob", 0.5) for seg in segments
        ]

        # Convert log prob to 0-1 scale (exp of avg_logprob)
        import math
        avg_confidence = sum(
            math.exp(lp) * (1 - nsp)
            for lp, nsp in zip(avg_logprobs, no_speech_probs)
        ) / len(segments)

        return min(max(avg_confidence, 0.0), 1.0)

    def _post_process_math(self, text: str) -> str:
        """
        Post-process transcript to handle math-specific phrases.
        Replaces spoken math with symbolic notation.
        """
        processed = text.lower()

        # Sort by length (longest first) to avoid partial replacements
        sorted_phrases = sorted(
            MATH_PHRASE_MAP.items(), key=lambda x: len(x[0]), reverse=True
        )

        for phrase, symbol in sorted_phrases:
            processed = processed.replace(phrase, f" {symbol} ")

        # Clean up extra spaces
        processed = " ".join(processed.split())

        return processed
