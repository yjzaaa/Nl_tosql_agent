"""Prompts Module

Provides prompt templates for NL to SQL agents.
"""

from .manager import (
    SQL_GENERATION_PROMPT,
    SQL_VALIDATION_PROMPT,
    RESULT_REVIEW_PROMPT,
    ANSWER_REFINEMENT_PROMPT,
    render_prompt_template
)

__all__ = [
    "SQL_GENERATION_PROMPT",
    "SQL_VALIDATION_PROMPT",
    "RESULT_REVIEW_PROMPT",
    "ANSWER_REFINEMENT_PROMPT",
    "render_prompt_template"
]
