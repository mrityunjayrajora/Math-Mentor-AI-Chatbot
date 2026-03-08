"""
Enumerations for the Math Mentor application.
"""

from enum import Enum


class InputMode(str, Enum):
    TEXT = "text"
    IMAGE = "image"
    AUDIO = "audio"


class MathTopic(str, Enum):
    ALGEBRA = "algebra"
    PROBABILITY = "probability"
    CALCULUS = "calculus"
    LINEAR_ALGEBRA = "linear_algebra"


class SolvingStrategy(str, Enum):
    ANALYTICAL = "analytical"
    NUMERICAL = "numerical"
    HYBRID = "hybrid"


class HITLStatus(str, Enum):
    NOT_REQUIRED = "not_required"
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    CORRECTED = "corrected"


class HITLTriggerReason(str, Enum):
    LOW_OCR_CONFIDENCE = "low_ocr_confidence"
    LOW_ASR_CONFIDENCE = "low_asr_confidence"
    PARSER_AMBIGUITY = "parser_ambiguity"
    LOW_VERIFIER_CONFIDENCE = "low_verifier_confidence"
    USER_REQUESTED = "user_requested"
