"""Prompt templates and instructions for the research assistant."""

from .analyst_prompts import format_analyst_instructions, format_regeneration_instructions
from .interview_prompts import (
    format_answer_instructions,
    format_question_instructions,
    get_search_instructions_as_system_message,
)
from .report_prompts import (
    format_conclusion_instructions,
    format_introduction_instructions,
    format_report_instructions,
    format_section_instructions,
)

__all__ = [
    "format_analyst_instructions",
    "format_regeneration_instructions",
    "format_question_instructions",
    "format_answer_instructions",
    "get_search_instructions_as_system_message",
    "format_section_instructions",
    "format_report_instructions",
    "format_introduction_instructions",
    "format_conclusion_instructions",
]
