"""Core schema definitions for the research assistant.

This module contains all Pydantic models used throughout the research assistant
application. These schemas define the structure and validation rules for analysts,
interview queries, and perspectives.

Example:
    Creating an analyst:
    
    >>> analyst = Analyst(
    ...     name="Dr. Sarah Chen",
    ...     role="AI Safety Researcher",
    ...     affiliation="OpenAI",
    ...     description="Focuses on alignment and safety concerns in LLMs"
    ... )
    >>> print(analyst.persona)
    Name: Dr. Sarah Chen
    Role: AI Safety Researcher
    Affiliation: OpenAI
    Description: Focuses on alignment and safety concerns in LLMs
"""

from typing import List, Optional
from pydantic import BaseModel, Field, field_validator, model_validator


class Analyst(BaseModel):
    """Represents an AI analyst persona for conducting research interviews.
    
    An analyst is characterized by their professional background, expertise area,
    and research focus. Each analyst conducts interviews from their unique perspective
    to gather insights on specific aspects of a research topic.
    
    Attributes:
        affiliation: Primary institution or organization the analyst represents.
        name: Full name of the analyst persona.
        role: Professional role or title of the analyst.
        description: Detailed description of the analyst's focus, concerns, and motives.
            Should clearly articulate what aspects of the topic they care about and why.
    
    Example:
        >>> analyst = Analyst(
        ...     name="Prof. Michael Roberts",
        ...     role="Economics Professor",
        ...     affiliation="Stanford University",
        ...     description="Specializes in market dynamics and economic impacts of AI"
        ... )
        >>> analyst.get_short_description()
        'Prof. Michael Roberts (Economics Professor at Stanford University)'
    """
    
    affiliation: str = Field(
        description="Primary affiliation of the analyst.",
        min_length=2,
        max_length=200,
    )
    name: str = Field(
        description="Name of the analyst.",
        min_length=2,
        max_length=100,
    )
    role: str = Field(
        description="Role of the analyst in the context of the topic.",
        min_length=2,
        max_length=150,
    )
    description: str = Field(
        description="Description of the analyst focus, concerns, and motives.",
        min_length=10,
        max_length=1000,
    )
    
    @field_validator("name", "role", "affiliation", "description")
    @classmethod
    def strip_whitespace(cls, v: str) -> str:
        """Remove leading and trailing whitespace from string fields.
        
        Args:
            v: The string value to validate.
            
        Returns:
            The trimmed string.
        """
        return v.strip()
    
    @field_validator("description")
    @classmethod
    def validate_description_content(cls, v: str) -> str:
        """Ensure description contains meaningful content.
        
        Args:
            v: The description string to validate.
            
        Returns:
            The validated description.
            
        Raises:
            ValueError: If description is too generic or lacks substance.
        """
        # Check for minimum word count
        word_count = len(v.split())
        if word_count < 5:
            raise ValueError(
                f"Description must contain at least 5 words, got {word_count}"
            )
        return v
    
    @property
    def persona(self) -> str:
        """Generate a formatted persona string for prompts.
        
        This property creates a structured text representation of the analyst
        that can be used in LLM prompts to establish context and persona.
        
        Returns:
            A formatted multi-line string containing all analyst information.
            
        Example:
            >>> analyst.persona
            'Name: Dr. Sarah Chen\\nRole: AI Safety Researcher\\n...'
        """
        return (
            f"Name: {self.name}\n"
            f"Role: {self.role}\n"
            f"Affiliation: {self.affiliation}\n"
            f"Description: {self.description}\n"
        )
    
    def get_short_description(self) -> str:
        """Get a concise one-line description of the analyst.
        
        Returns:
            A brief description in the format: "Name (Role at Affiliation)".
            
        Example:
            >>> analyst.get_short_description()
            'Dr. Sarah Chen (AI Safety Researcher at OpenAI)'
        """
        return f"{self.name} ({self.role} at {self.affiliation})"
    
    def get_focus_area(self) -> str:
        """Extract the primary focus area from the description.
        
        Returns:
            The first sentence of the description, typically containing
            the main focus area.
            
        Example:
            >>> analyst.get_focus_area()
            'Focuses on alignment and safety concerns in LLMs.'
        """
        # Return first sentence as focus area
        description_sentences = self.description.split(".")
        if description_sentences:
            return description_sentences[0].strip() + "."
        return self.description
    
    class Config:
        """Pydantic model configuration."""
        
        json_schema_extra = {
            "example": {
                "name": "Dr. Emily Zhang",
                "role": "Climate Scientist",
                "affiliation": "MIT Climate Research Institute",
                "description": (
                    "Focuses on the intersection of AI and climate modeling. "
                    "Particularly interested in how machine learning can improve "
                    "climate predictions and inform policy decisions."
                ),
            }
        }


class Perspectives(BaseModel):
    """Collection of analyst perspectives for multi-faceted research.
    
    This model represents a team of analysts, each bringing a unique perspective
    to the research topic. The diversity of analysts ensures comprehensive coverage
    of the subject matter.
    
    Attributes:
        analysts: List of Analyst instances representing different viewpoints.
            Should contain between 1 and 10 analysts for optimal coverage.
    
    Example:
        >>> perspectives = Perspectives(analysts=[
        ...     Analyst(name="Alice", role="Engineer", affiliation="Tech Corp",
        ...             description="Focuses on technical implementation"),
        ...     Analyst(name="Bob", role="Ethicist", affiliation="University",
        ...             description="Focuses on ethical implications")
        ... ])
        >>> perspectives.get_analyst_count()
        2
    """
    
    analysts: List[Analyst] = Field(
        description="Comprehensive list of analysts with their roles and affiliations.",
        min_length=1,
        max_length=10,
    )
    
    @field_validator("analysts")
    @classmethod
    def validate_unique_names(cls, v: List[Analyst]) -> List[Analyst]:
        """Ensure all analyst names are unique.
        
        Args:
            v: List of analysts to validate.
            
        Returns:
            The validated list of analysts.
            
        Raises:
            ValueError: If duplicate analyst names are found.
        """
        names = [analyst.name for analyst in v]
        if len(names) != len(set(names)):
            duplicates = [name for name in names if names.count(name) > 1]
            raise ValueError(
                f"Duplicate analyst names found: {', '.join(set(duplicates))}"
            )
        return v
    
    @field_validator("analysts")
    @classmethod
    def validate_diverse_roles(cls, v: List[Analyst]) -> List[Analyst]:
        """Warn if analysts have very similar roles.
        
        While not enforcing strict uniqueness (as similar roles can have
        different focuses), this validator checks for potential redundancy.
        
        Args:
            v: List of analysts to validate.
            
        Returns:
            The validated list of analysts.
        """
        roles = [analyst.role.lower() for analyst in v]
        if len(roles) != len(set(roles)) and len(v) > 1:
            # This is a warning-level issue, not an error
            # In production, you might want to log this
            pass
        return v
    
    def get_analyst_count(self) -> int:
        """Get the total number of analysts.
        
        Returns:
            Integer count of analysts in the collection.
        """
        return len(self.analysts)
    
    def get_analyst_by_name(self, name: str) -> Optional[Analyst]:
        """Retrieve an analyst by their name.
        
        Args:
            name: The name of the analyst to find.
            
        Returns:
            The Analyst instance if found, None otherwise.
            
        Example:
            >>> analyst = perspectives.get_analyst_by_name("Dr. Emily Zhang")
            >>> if analyst:
            ...     print(analyst.role)
        """
        for analyst in self.analysts:
            if analyst.name == name:
                return analyst
        return None
    
    def get_affiliations(self) -> List[str]:
        """Get a list of all unique affiliations.
        
        Returns:
            List of unique affiliation strings.
            
        Example:
            >>> perspectives.get_affiliations()
            ['MIT', 'Stanford University', 'OpenAI']
        """
        return list(set(analyst.affiliation for analyst in self.analysts))
    
    def get_summary(self) -> str:
        """Generate a summary of all analysts in the collection.
        
        Returns:
            A formatted string summarizing each analyst.
            
        Example:
            >>> print(perspectives.get_summary())
            Analyst Team (2 members):
            1. Dr. Emily Zhang - Climate Scientist at MIT
            2. Prof. John Doe - Economist at Stanford
        """
        summary_lines = [f"Analyst Team ({self.get_analyst_count()} members):"]
        for i, analyst in enumerate(self.analysts, 1):
            summary_lines.append(
                f"{i}. {analyst.name} - {analyst.role} at {analyst.affiliation}"
            )
        return "\n".join(summary_lines)
    
    class Config:
        """Pydantic model configuration."""
        
        json_schema_extra = {
            "example": {
                "analysts": [
                    {
                        "name": "Dr. Emily Zhang",
                        "role": "Climate Scientist",
                        "affiliation": "MIT Climate Research Institute",
                        "description": "Focuses on AI applications in climate modeling",
                    },
                    {
                        "name": "Prof. Michael Chen",
                        "role": "Policy Analyst",
                        "affiliation": "Georgetown University",
                        "description": "Examines policy implications of climate technology",
                    },
                ]
            }
        }


class SearchQuery(BaseModel):
    """Represents a structured search query for information retrieval.
    
    This model encapsulates search queries generated from interview conversations,
    optimized for web search engines and knowledge bases.
    
    Attributes:
        search_query: The search query string. Can be None if no query is needed.
            Should be concise (1-10 words) and well-structured for optimal results.
    
    Example:
        >>> query = SearchQuery(search_query="climate change AI applications 2024")
        >>> query.get_word_count()
        5
    """
    
    search_query: Optional[str] = Field(
        None,
        description="Search query for retrieval.",
        max_length=500,
    )
    
    @field_validator("search_query")
    @classmethod
    def validate_and_clean_query(cls, v: Optional[str]) -> Optional[str]:
        """Clean and validate the search query.
        
        Args:
            v: The search query string to validate.
            
        Returns:
            The cleaned and validated query, or None.
        """
        if v is None:
            return v
        
        # Strip whitespace and normalize
        cleaned = " ".join(v.split())
        
        # Warn if query is very short (might be too vague)
        if len(cleaned) < 3:
            # In production, you might want to log this warning
            pass
        
        return cleaned if cleaned else None
    
    @model_validator(mode="after")
    def validate_query_structure(self) -> "SearchQuery":
        """Validate the overall structure of the search query.
        
        Returns:
            The validated SearchQuery instance.
        """
        if self.search_query:
            # Check for excessively long queries
            word_count = len(self.search_query.split())
            if word_count > 15:
                # Long queries might not perform well
                # In production, you might want to log this
                pass
        
        return self
    
    def get_word_count(self) -> int:
        """Get the number of words in the search query.
        
        Returns:
            Integer count of words, or 0 if query is None.
            
        Example:
            >>> query = SearchQuery(search_query="AI climate change")
            >>> query.get_word_count()
            3
        """
        if not self.search_query:
            return 0
        return len(self.search_query.split())
    
    def is_empty(self) -> bool:
        """Check if the search query is empty or None.
        
        Returns:
            True if query is None or empty string, False otherwise.
        """
        return not self.search_query or not self.search_query.strip()
    
    def to_dict(self) -> dict:
        """Convert to dictionary format for API calls.
        
        Returns:
            Dictionary with 'query' key for compatibility with search APIs.
            
        Example:
            >>> query.to_dict()
            {'query': 'AI climate change'}
        """
        return {"query": self.search_query}
    
    class Config:
        """Pydantic model configuration."""
        
        json_schema_extra = {
            "example": {
                "search_query": "large language models scaling laws 2024"
            }
        }


# Type aliases for common use cases
AnalystList = List[Analyst]
SearchQueries = List[SearchQuery]


# Validation utilities
def validate_analyst_diversity(analysts: List[Analyst]) -> bool:
    """Check if a list of analysts has sufficient diversity.
    
    This function evaluates whether analysts cover different roles and
    affiliations, which is important for comprehensive research coverage.
    
    Args:
        analysts: List of Analyst instances to evaluate.
        
    Returns:
        True if analysts show good diversity, False otherwise.
        
    Example:
        >>> analysts = [analyst1, analyst2, analyst3]
        >>> is_diverse = validate_analyst_diversity(analysts)
        >>> if not is_diverse:
        ...     print("Consider adding analysts with different perspectives")
    """
    if len(analysts) <= 1:
        return True
    
    roles = set(analyst.role for analyst in analysts)
    affiliations = set(analyst.affiliation for analyst in analysts)
    
    # Good diversity: unique roles and at least some affiliation diversity
    unique_roles_ratio = len(roles) / len(analysts)
    unique_affiliation_ratio = len(affiliations) / len(analysts)
    
    # At least 70% unique roles and 50% unique affiliations
    return unique_roles_ratio >= 0.7 and unique_affiliation_ratio >= 0.5


def create_analyst_from_dict(data: dict) -> Analyst:
    """Factory function to create an Analyst from a dictionary.
    
    This function provides a convenient way to create Analyst instances
    from dictionary data, with additional validation and error handling.
    
    Args:
        data: Dictionary containing analyst information with keys:
            'name', 'role', 'affiliation', 'description'.
            
    Returns:
        A validated Analyst instance.
        
    Raises:
        ValueError: If required fields are missing or invalid.
        
    Example:
        >>> analyst_data = {
        ...     "name": "Dr. Smith",
        ...     "role": "Researcher",
        ...     "affiliation": "MIT",
        ...     "description": "Focuses on AI ethics and safety"
        ... }
        >>> analyst = create_analyst_from_dict(analyst_data)
    """
    required_fields = {"name", "role", "affiliation", "description"}
    missing_fields = required_fields - set(data.keys())
    
    if missing_fields:
        raise ValueError(
            f"Missing required fields: {', '.join(missing_fields)}"
        )
    
    return Analyst(**data)
