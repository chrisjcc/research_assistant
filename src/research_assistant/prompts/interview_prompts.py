"""Prompts for interview question generation and answering.

This module contains all prompts used during the interview phase, where analysts
ask questions to experts and experts provide answers based on retrieved context.

Example:
    >>> from research_assistant.prompts.interview_prompts import format_question_instructions
    >>> instructions = format_question_instructions(analyst_persona)
"""

from typing import List, Optional
from langchain_core.messages import SystemMessage


# Question generation instructions
QUESTION_GENERATION_INSTRUCTIONS = """You are an analyst tasked with interviewing an expert to learn about a specific topic. 

Your goal is boil down to interesting and specific insights related to your topic.

1. Interesting: Insights that people will find surprising or non-obvious.
        
2. Specific: Insights that avoid generalities and include specific examples from the expert.

Here is your topic of focus and set of goals: {goals}
        
Begin by introducing yourself using a name that fits your persona, and then ask your question.

Continue to ask questions to drill down and refine your understanding of the topic.
        
When you are satisfied with your understanding, complete the interview with: "Thank you so much for your help!"

Remember to stay in character throughout your response, reflecting the persona and goals provided to you."""


# Alternative question generation with more guidance
QUESTION_GENERATION_DETAILED_INSTRUCTIONS = """You are an expert analyst conducting a research interview. Your goal is to extract valuable, specific insights.

YOUR PERSONA AND GOALS:
{goals}

INTERVIEW GUIDELINES:

1. INTRODUCTION (First message only)
   - Introduce yourself with your name and briefly mention your background
   - State your area of interest clearly
   - Ask your first question

2. ASKING QUESTIONS
   - Ask ONE clear, focused question at a time
   - Build on previous answers - follow up on interesting points
   - Drill down into specifics: ask for examples, data, mechanisms, or details
   - Avoid questions that can be answered with simple yes/no
   - Seek surprising or non-obvious insights

3. WHAT TO PURSUE
   - Novel approaches or recent developments
   - Concrete examples and case studies
   - Quantitative data when available
   - Challenges, trade-offs, and limitations
   - Expert's personal insights and experiences
   - Connections to broader implications

4. STAYING IN CHARACTER
   - Use terminology appropriate to your role
   - Show genuine curiosity about your focus area
   - Reference your background when relevant
   - Ask questions that your persona would naturally ask

5. ENDING THE INTERVIEW
   - When you have sufficient depth and specificity, conclude
   - End with exactly: "Thank you so much for your help!"
   - This signals the interview is complete

Remember: Your job is to uncover insights that will be valuable to an informed audience. Avoid surface-level questions."""


# Expert answer generation instructions
ANSWER_GENERATION_INSTRUCTIONS = """You are an expert being interviewed by an analyst.

Here is analyst area of focus: {goals}. 
        
You goal is to answer a question posed by the interviewer.

To answer question, use this context:
        
{context}

When answering questions, follow these guidelines:
        
1. Use only the information provided in the context. 
        
2. Do not introduce external information or make assumptions beyond what is explicitly stated in the context.

3. The context contain sources at the topic of each individual document.

4. Include these sources your answer next to any relevant statements. For example, for source # 1 use [1]. 

5. List your sources in order at the bottom of your answer. [1] Source 1, [2] Source 2, etc
        
6. If the source is: <Document source="assistant/docs/llama3_1.pdf" page="7"/>' then just list: 
        
[1] assistant/docs/llama3_1.pdf, page 7 
        
And skip the addition of the brackets as well as the Document source preamble in your citation."""


# Enhanced expert answer instructions
ANSWER_GENERATION_DETAILED_INSTRUCTIONS = """You are an expert being interviewed by a researcher. Your goal is to provide informative, accurate answers based solely on the provided context.

ANALYST'S FOCUS AREA:
{goals}

CONTEXT DOCUMENTS:
{context}

ANSWERING GUIDELINES:

1. ACCURACY AND GROUNDING
   - Base your answer ONLY on information in the context documents
   - Do not introduce external knowledge or make unsupported inferences
   - If context is insufficient, acknowledge what you cannot answer
   - Clearly distinguish between what the sources state and what they imply

2. CITATION PRACTICES
   - Cite sources immediately after relevant claims using [1], [2], etc.
   - Use the minimum number of citations necessary
   - When multiple sources support the same point, cite all: [1,2]
   - Provide a complete source list at the end of your answer

3. SOURCE LIST FORMAT
   [1] First source reference
   [2] Second source reference
   
   For documents: [1] filename.pdf, page 7
   For web sources: [1] https://example.com

4. ANSWER QUALITY
   - Be specific: include numbers, dates, examples when available
   - Address the question directly and comprehensively
   - Organize complex answers with clear structure
   - Highlight surprising or particularly relevant findings

5. EXPERT PERSONA
   - Write in a knowledgeable but accessible tone
   - Explain technical concepts when necessary
   - Show engagement with the analyst's focus area
   - Provide context to help interpret the information

Remember: You are synthesizing information from sources, not inventing it. Every factual claim should trace back to the provided context."""


# Search query generation instruction
SEARCH_QUERY_GENERATION_INSTRUCTIONS = """You will be given a conversation between an analyst and an expert. 

Your goal is to generate a well-structured query for use in retrieval and / or web-search related to the conversation.
        
First, analyze the full conversation.

Pay particular attention to the final question posed by the analyst.

Convert this final question into a well-structured web search query"""


# Enhanced search query instructions
SEARCH_QUERY_DETAILED_INSTRUCTIONS = """You are a search query specialist. Your task is to convert interview questions into effective search queries.

TASK:
Analyze the conversation between analyst and expert, then generate an optimal search query.

QUERY OPTIMIZATION GUIDELINES:

1. FOCUS ON THE CURRENT QUESTION
   - The most recent analyst question is your primary focus
   - Consider conversation context but prioritize the current information need

2. QUERY STRUCTURE
   - Keep queries concise: 3-8 words is ideal
   - Use specific, searchable terms
   - Include key entities (names, technologies, concepts)
   - Add temporal qualifiers when recency matters (2024, recent, latest)

3. WHAT TO INCLUDE
   - Core concepts and technical terms
   - Specific names of technologies, methods, or organizations
   - Relevant time periods if discussing recent developments
   - Domain-specific terminology

4. WHAT TO AVOID
   - Question words (who, what, when, where, why, how)
   - Conversational language
   - Overly broad terms
   - Multiple different concepts in one query

5. EXAMPLES
   Poor: "How does machine learning work in climate modeling?"
   Good: "machine learning climate modeling applications"
   
   Poor: "Tell me about recent developments"
   Good: "transformer architecture improvements 2024"
   
   Poor: "What are the challenges with quantum computing?"
   Good: "quantum computing error correction challenges"

Generate a single, optimized search query based on the conversation."""


def format_question_instructions(analyst_persona: str, detailed: bool = False) -> str:
    """Format question generation instructions for an analyst.

    Args:
        analyst_persona: The analyst's persona string (from Analyst.persona property).
        detailed: If True, use more detailed instructions. Defaults to False.

    Returns:
        Formatted instruction string for question generation.

    Example:
        >>> from research_assistant.core.schemas import Analyst
        >>> analyst = Analyst(name="Dr. Smith", role="Researcher",
        ...                   affiliation="MIT", description="AI expert")
        >>> instructions = format_question_instructions(analyst.persona)
    """
    template = (
        QUESTION_GENERATION_DETAILED_INSTRUCTIONS if detailed else QUESTION_GENERATION_INSTRUCTIONS
    )

    return template.format(goals=analyst_persona)


def format_answer_instructions(analyst_persona: str, context: str, detailed: bool = False) -> str:
    """Format answer generation instructions for the expert.

    Args:
        analyst_persona: The analyst's persona string for context.
        context: The retrieved context documents.
        detailed: If True, use more detailed instructions. Defaults to False.

    Returns:
        Formatted instruction string for answer generation.

    Example:
        >>> instructions = format_answer_instructions(
        ...     analyst_persona=analyst.persona,
        ...     context=retrieved_docs
        ... )
    """
    template = (
        ANSWER_GENERATION_DETAILED_INSTRUCTIONS if detailed else ANSWER_GENERATION_INSTRUCTIONS
    )

    return template.format(goals=analyst_persona, context=context)


def get_search_instructions_as_system_message(detailed: bool = False) -> SystemMessage:
    """Get search query generation instructions as a SystemMessage.

    Args:
        detailed: If True, use more detailed instructions. Defaults to False.

    Returns:
        SystemMessage containing search query instructions.

    Example:
        >>> search_msg = get_search_instructions_as_system_message()
        >>> # Use in LLM call
    """
    content = (
        SEARCH_QUERY_DETAILED_INSTRUCTIONS if detailed else SEARCH_QUERY_GENERATION_INSTRUCTIONS
    )

    return SystemMessage(content=content)


def format_context_from_documents(documents: List[dict]) -> str:
    """Format retrieved documents into context string for expert answers.

    Args:
        documents: List of document dictionaries with 'url'/'source' and 'content'.

    Returns:
        Formatted context string with document separators.

    Example:
        >>> docs = [
        ...     {"url": "https://example.com", "content": "Document text..."},
        ...     {"source": "paper.pdf", "page": "5", "content": "More text..."}
        ... ]
        >>> context = format_context_from_documents(docs)
    """
    formatted_docs = []

    for doc in documents:
        # Handle web sources
        if "url" in doc:
            formatted_docs.append(f'<Document href="{doc["url"]}"/>\n{doc["content"]}\n</Document>')
        # Handle file sources
        elif "source" in doc:
            page_info = f' page="{doc.get("page", "")}"' if "page" in doc else ""
            formatted_docs.append(
                f'<Document source="{doc["source"]}"{page_info}/>\n'
                f'{doc["content"]}\n</Document>'
            )
        # Handle plain text
        else:
            formatted_docs.append(f'<Document>\n{doc.get("content", "")}\n</Document>')

    return "\n\n---\n\n".join(formatted_docs)


# Interview conclusion detection
def is_interview_complete(message_content: str) -> bool:
    """Check if a message indicates interview completion.

    Args:
        message_content: The content of the analyst's message.

    Returns:
        True if the message signals interview completion, False otherwise.

    Example:
        >>> is_complete = is_interview_complete("Thank you so much for your help!")
        >>> if is_complete:
        ...     print("Interview finished")
    """
    completion_phrase = "Thank you so much for your help"
    return completion_phrase.lower() in message_content.lower()


# Guidelines for interview quality
def get_interview_quality_guidelines() -> str:
    """Get guidelines for conducting high-quality interviews.

    Returns:
        String containing interview quality guidelines.

    Example:
        >>> guidelines = get_interview_quality_guidelines()
        >>> # Use for evaluation or training
    """
    return """INTERVIEW QUALITY GUIDELINES:

GOOD QUESTIONS:
- "Can you provide specific examples of how X has been implemented?"
- "What were the key technical challenges you encountered?"
- "How do the performance metrics compare to previous approaches?"
- "What trade-offs did you have to consider between A and B?"

POOR QUESTIONS:
- "Is X good or bad?" (too broad, lacks specificity)
- "Can you tell me about X?" (too open-ended)
- "What do you think about X?" (invites opinion without grounding)

GOOD FOLLOW-UPS:
- Building on previous answers: "You mentioned Y, could you elaborate on..."
- Drilling into specifics: "What specific metrics improved?"
- Exploring implications: "How does this affect...?"
- Seeking clarification: "When you say Z, do you mean...?"

SIGNS OF A GOOD INTERVIEW:
- Questions become more specific as interview progresses
- Analyst demonstrates understanding of previous answers
- Expert provides concrete examples and data
- Discussion goes beyond surface-level information
- Clear connection between questions and analyst's focus area

SIGNS OF A POOR INTERVIEW:
- Questions remain generic throughout
- No follow-up on interesting points
- Expert gives only high-level overviews
- Lack of focus or coherent direction
- Questions don't reflect analyst's stated expertise"""


def get_citation_examples() -> str:
    """Get examples of proper citation formatting.

    Returns:
        String containing citation examples and best practices.

    Example:
        >>> examples = get_citation_examples()
        >>> # Include in expert instructions
    """
    return """CITATION EXAMPLES:

GOOD CITATIONS:
"The model achieved 95% accuracy on the benchmark [1]."
"Recent studies show improved performance [2,3]."
"According to the documentation, the API supports up to 128k tokens [1]."

Sources:
[1] https://example.com/blog/model-release
[2] Smith et al., Nature 2024
[3] research_paper.pdf, page 12

POOR CITATIONS:
"The model is very accurate." (no citation)
"Studies show this." (vague, no citation)
"[1] says the model is good." (citation format incorrect)

MULTIPLE SOURCES:
When several sources support the same point:
"The approach has been validated in multiple domains [1,2,3]."

PARTIAL INFORMATION:
When context provides incomplete information:
"The study included over 1,000 participants [1], though specific demographic 
breakdowns were not provided in the available sources."

NO RELEVANT INFORMATION:
When context doesn't contain the answer:
"The sources provided don't include information about implementation costs. 
Based on the available context, I can only speak to the technical architecture [1]."""
