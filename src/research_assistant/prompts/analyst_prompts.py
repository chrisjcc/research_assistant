"""Prompts for analyst persona creation.

This module contains all prompts and instructions used in the analyst generation
phase of the research workflow. These prompts guide the LLM in creating diverse,
well-defined analyst personas that will conduct research interviews.

Example:
    >>> from research_assistant.prompts.analyst_prompts import format_analyst_instructions
    >>> instructions = format_analyst_instructions(
    ...     topic="AI Safety",
    ...     max_analysts=3,
    ...     human_feedback="Focus on technical aspects"
    ... )
"""

from typing import Optional


# Main analyst creation instruction template
ANALYST_CREATION_INSTRUCTIONS = """You are tasked with creating a set of AI analyst personas. Follow these instructions carefully:

1. First, review the research topic:
{topic}
        
2. Examine any editorial feedback that has been optionally provided to guide creation of the analysts: 
        
{human_analyst_feedback}
    
3. Determine the most interesting themes based upon documents and / or feedback above.
                    
4. Pick the top {max_analysts} themes.

5. Assign one analyst to each theme."""


# Alternative instruction template with more detailed guidance
ANALYST_CREATION_DETAILED_INSTRUCTIONS = """You are an expert at creating diverse analyst personas for comprehensive research coverage.

Your task is to create {max_analysts} AI analyst personas who will investigate different aspects of this research topic:

TOPIC: {topic}

EDITORIAL FEEDBACK (if provided):
{human_analyst_feedback}

INSTRUCTIONS:

1. ANALYZE THE TOPIC
   - Identify the key domains, disciplines, or perspectives relevant to this topic
   - Consider technical, social, ethical, economic, and policy dimensions
   - Think about both immediate and long-term implications

2. SELECT DIVERSE THEMES
   - Choose {max_analysts} distinct themes that provide comprehensive coverage
   - Ensure themes are complementary, not overlapping
   - Prioritize themes that will yield the most interesting and actionable insights
   - Consider: What would an expert audience want to know?

3. CREATE ANALYST PERSONAS
   For each theme, create an analyst with:
   - A realistic name that fits their background
   - A specific professional role (not generic titles like "Analyst" or "Expert")
   - A credible affiliation (university, company, research institute, etc.)
   - A detailed description (50-100 words) that includes:
     * Their area of expertise within the theme
     * What specific questions or concerns they bring
     * Why their perspective is valuable for this research
     * What unique insights they might uncover

4. ENSURE DIVERSITY
   - Vary affiliations across academia, industry, policy, and civil society
   - Include different levels of seniority and specialization
   - Consider geographic and institutional diversity
   - Balance theoretical and practical perspectives

Remember: These analysts will conduct interviews to gather information. They should be curious, knowledgeable, and focused on uncovering insights that might not be obvious to a general audience."""


# System message for analyst regeneration
ANALYST_REGENERATION_INSTRUCTIONS = """The analysts you previously created have received feedback. Please revise them according to this guidance:

ORIGINAL TOPIC: {topic}

FEEDBACK: {human_analyst_feedback}

Please create a new set of {max_analysts} analysts that addresses the feedback while maintaining diversity and comprehensive coverage of the topic.

Focus on:
1. Addressing the specific concerns raised in the feedback
2. Maintaining high quality and diverse perspectives
3. Ensuring each analyst has a clear, distinct focus area"""


# Instruction for when no feedback is provided
ANALYST_CREATION_NO_FEEDBACK = """You are tasked with creating a set of AI analyst personas. Follow these instructions carefully:

1. First, review the research topic:
{topic}

2. Determine the {max_analysts} most interesting and important themes to investigate for this topic.

3. For each theme, create a distinct analyst persona with:
   - A realistic name
   - A specific professional role
   - A credible affiliation
   - A detailed description of their expertise and focus

4. Ensure the analysts provide diverse, complementary perspectives that will result in comprehensive research coverage."""


def format_analyst_instructions(
    topic: str, max_analysts: int, human_feedback: Optional[str] = None, detailed: bool = False
) -> str:
    """Format analyst creation instructions with provided parameters.

    Args:
        topic: The research topic for analyst creation.
        max_analysts: Maximum number of analysts to create.
        human_feedback: Optional human feedback for analyst refinement.
            If None or empty, indicates initial creation without feedback.
        detailed: If True, use more detailed instructions. Defaults to False.

    Returns:
        Formatted instruction string ready for LLM consumption.

    Example:
        >>> instructions = format_analyst_instructions(
        ...     topic="Quantum Computing",
        ...     max_analysts=3,
        ...     human_feedback="Focus on practical applications"
        ... )
    """
    # Clean and prepare feedback
    feedback = human_feedback if human_feedback else ""
    feedback = feedback.strip()

    # If no feedback provided, use simplified template
    if not feedback:
        feedback = "No specific feedback provided. Use your best judgment to create diverse, high-quality analyst personas."

    # Choose template based on detailed flag
    if detailed:
        template = ANALYST_CREATION_DETAILED_INSTRUCTIONS
    else:
        template = ANALYST_CREATION_INSTRUCTIONS

    # Format and return
    return template.format(topic=topic, max_analysts=max_analysts, human_analyst_feedback=feedback)


def format_regeneration_instructions(topic: str, max_analysts: int, human_feedback: str) -> str:
    """Format instructions for regenerating analysts based on feedback.

    This is used when human reviewers provide feedback on initially generated
    analysts and request modifications.

    Args:
        topic: The research topic.
        max_analysts: Maximum number of analysts to create.
        human_feedback: Human feedback explaining desired changes.

    Returns:
        Formatted regeneration instruction string.

    Example:
        >>> instructions = format_regeneration_instructions(
        ...     topic="AI Ethics",
        ...     max_analysts=3,
        ...     human_feedback="Need more focus on policy perspectives"
        ... )
    """
    return ANALYST_REGENERATION_INSTRUCTIONS.format(
        topic=topic, max_analysts=max_analysts, human_analyst_feedback=human_feedback
    )


def get_analyst_quality_criteria() -> str:
    """Get the quality criteria for analyst creation.

    Returns a description of what makes a good analyst persona. This can be
    used for evaluation or as additional context in prompts.

    Returns:
        String describing quality criteria.

    Example:
        >>> criteria = get_analyst_quality_criteria()
        >>> print(criteria)
    """
    return """QUALITY CRITERIA FOR ANALYST PERSONAS:

1. SPECIFICITY
   - Analysts should have specific expertise, not general knowledge
   - Focus areas should be narrow enough to be actionable
   - Avoid vague descriptions like "interested in various aspects"

2. CREDIBILITY
   - Names should be realistic and culturally appropriate
   - Affiliations should be real institutions or plausible organizations
   - Roles should match the affiliation type (e.g., "Professor" at universities)

3. DIVERSITY
   - Different institutional types (academic, industry, government, NGO)
   - Various disciplines and methodological approaches
   - Different levels of abstraction (theoretical vs. applied)
   - Geographic and cultural diversity when relevant

4. COMPLEMENTARITY
   - Analysts should cover different aspects of the topic
   - Perspectives should be complementary, not redundant
   - Together, they should provide comprehensive coverage

5. INTERVIEW POTENTIAL
   - Each analyst should have clear questions they would want answered
   - Their focus should lead to interesting, specific insights
   - They should be able to drill down into details, not just general overviews"""


def get_example_analysts() -> str:
    """Get example analyst personas for reference.

    Provides concrete examples of well-crafted analyst personas that can serve
    as templates or reference points.

    Returns:
        String containing example analyst definitions.

    Example:
        >>> examples = get_example_analysts()
        >>> # Use in few-shot prompting
    """
    return """EXAMPLE ANALYST PERSONAS:

Example 1 - Technology Topic:
Name: Dr. Sarah Chen
Role: Machine Learning Research Scientist
Affiliation: Google DeepMind
Description: Specializes in transformer architectures and efficient training methods. 
Particularly interested in how scaling laws apply to different model architectures and 
training regimes. Wants to understand the practical engineering challenges and 
trade-offs in training large language models, including computational costs, 
memory requirements, and optimization strategies.

Example 2 - Policy Topic:
Name: Ambassador James Mitchell
Role: Senior Fellow, International Security Program
Affiliation: Council on Foreign Relations
Description: Former diplomat with 25 years of experience in arms control negotiations. 
Focuses on the intersection of emerging technologies and international security frameworks. 
Concerned with how AI capabilities might affect strategic stability, the applicability of 
existing international law, and the prospects for meaningful governance mechanisms. 
Seeks to understand technical capabilities well enough to inform policy recommendations.

Example 3 - Social Sciences Topic:
Name: Prof. Maria Rodriguez
Role: Associate Professor of Science & Technology Studies
Affiliation: MIT
Description: Uses ethnographic methods to study how technologies are developed and 
deployed in organizational contexts. Interested in the social dynamics of AI research labs, 
how different communities understand and frame AI risks, and whose voices are included or 
excluded in AI governance discussions. Particularly attuned to power dynamics and 
structural inequalities."""


# Prompt for validating generated analysts
ANALYST_VALIDATION_PROMPT = """Review the following analyst personas and assess their quality:

{analysts}

Evaluate based on these criteria:
1. Are the analysts sufficiently diverse in perspectives and backgrounds?
2. Do they have specific, well-defined areas of focus?
3. Are their affiliations and roles credible?
4. Together, do they provide comprehensive coverage of the topic: {topic}?
5. Is there any significant overlap or redundancy?

Provide:
- An overall quality score (1-10)
- Specific strengths
- Specific weaknesses or gaps
- Recommendations for improvement"""


def format_analyst_validation_prompt(analysts_text: str, topic: str) -> str:
    """Format a prompt for validating generated analysts.

    Args:
        analysts_text: Text description of generated analysts.
        topic: The research topic.

    Returns:
        Formatted validation prompt.

    Example:
        >>> validation = format_analyst_validation_prompt(
        ...     analysts_text=analyst_descriptions,
        ...     topic="Climate Change"
        ... )
    """
    return ANALYST_VALIDATION_PROMPT.format(analysts=analysts_text, topic=topic)
