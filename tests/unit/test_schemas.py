"""Unit tests for core schemas.

Tests Pydantic models for analysts, perspectives, and search queries.
"""

import pytest
from pydantic import ValidationError

from research_assistant.core.schemas import (
    Analyst,
    Perspectives,
    SearchQuery,
    validate_analyst_diversity,
    create_analyst_from_dict,
)


# ============================================================================
# Analyst Model Tests
# ============================================================================


class TestAnalyst:
    """Test suite for Analyst model."""

    def test_create_valid_analyst(self, sample_analyst):
        """Test creating a valid analyst."""
        assert sample_analyst.name == "Dr. Alice Smith"
        assert sample_analyst.role == "AI Researcher"
        assert sample_analyst.affiliation == "MIT"
        assert "machine learning" in sample_analyst.description.lower()

    def test_analyst_persona_property(self, sample_analyst):
        """Test persona property generation."""
        persona = sample_analyst.persona

        assert "Name: Dr. Alice Smith" in persona
        assert "Role: AI Researcher" in persona
        assert "Affiliation: MIT" in persona
        assert "Description:" in persona

    def test_analyst_short_description(self, sample_analyst):
        """Test short description method."""
        short_desc = sample_analyst.get_short_description()

        assert "Dr. Alice Smith" in short_desc
        assert "AI Researcher" in short_desc
        assert "MIT" in short_desc

    def test_analyst_focus_area(self, sample_analyst):
        """Test focus area extraction."""
        focus = sample_analyst.get_focus_area()

        assert isinstance(focus, str)
        assert len(focus) > 0
        assert focus.endswith(".")

    def test_analyst_name_validation_min_length(self):
        """Test name minimum length validation."""
        with pytest.raises(ValidationError) as exc_info:
            Analyst(
                name="A",  # Too short
                role="Researcher",
                affiliation="University",
                description="Test expert specializing in comprehensive testing",
            )

        assert "name" in str(exc_info.value).lower()

    def test_analyst_whitespace_stripping(self):
        """Test whitespace is stripped from fields."""
        analyst = Analyst(
            name="  Dr. Test  ",
            role="  Researcher  ",
            affiliation="  University  ",
            description="  Test expert specializing in comprehensive testing  ",
        )

        assert analyst.name == "Dr. Test"
        assert analyst.role == "Researcher"
        assert analyst.affiliation == "University"
        assert analyst.description == "Test expert specializing in comprehensive testing"

    def test_analyst_description_word_count(self):
        """Test description must have minimum words."""
        with pytest.raises(ValidationError):
            Analyst(
                name="Dr. Test",
                role="Researcher",
                affiliation="University",
                description="Too short",  # Less than 5 words
            )

    def test_analyst_field_max_lengths(self):
        """Test field maximum length validation."""
        # Name too long
        with pytest.raises(ValidationError):
            Analyst(
                name="A" * 101,  # Exceeds max_length=100
                role="Researcher",
                affiliation="University",
                description="Valid description here",
            )

    def test_analyst_json_schema_example(self):
        """Test JSON schema example is valid."""
        example = Analyst.model_config["json_schema_extra"]["example"]
        analyst = Analyst(**example)

        assert analyst.name == "Dr. Emily Zhang"
        assert "MIT" in analyst.affiliation


# ============================================================================
# Perspectives Model Tests
# ============================================================================


class TestPerspectives:
    """Test suite for Perspectives model."""

    def test_create_perspectives(self, sample_analysts):
        """Test creating perspectives with analysts."""
        perspectives = Perspectives(analysts=sample_analysts)

        assert len(perspectives.analysts) == 3
        assert all(isinstance(a, Analyst) for a in perspectives.analysts)

    def test_get_analyst_count(self, sample_perspectives):
        """Test analyst count method."""
        count = sample_perspectives.get_analyst_count()

        assert count == 3
        assert count == len(sample_perspectives.analysts)

    def test_get_analyst_by_name(self, sample_perspectives):
        """Test retrieving analyst by name."""
        analyst = sample_perspectives.get_analyst_by_name("Dr. Alice Smith")

        assert analyst is not None
        assert analyst.name == "Dr. Alice Smith"

        # Test not found
        not_found = sample_perspectives.get_analyst_by_name("Nonexistent")
        assert not_found is None

    def test_get_affiliations(self, sample_perspectives):
        """Test getting unique affiliations."""
        affiliations = sample_perspectives.get_affiliations()

        assert "MIT" in affiliations
        assert "Stanford" in affiliations
        assert "Google" in affiliations
        assert len(affiliations) == 3

    def test_get_summary(self, sample_perspectives):
        """Test perspectives summary generation."""
        summary = sample_perspectives.get_summary()

        assert "Analyst Team (3 members)" in summary
        assert "Dr. Alice Smith" in summary
        assert "Prof. Bob Johnson" in summary

    def test_unique_names_validation(self, sample_analyst):
        """Test that duplicate analyst names are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            Perspectives(analysts=[sample_analyst, sample_analyst])

        error_msg = str(exc_info.value).lower()
        assert "duplicate" in error_msg or "unique" in error_msg

    def test_min_max_analysts(self):
        """Test minimum and maximum analyst constraints."""
        # Empty list should fail
        with pytest.raises(ValidationError):
            Perspectives(analysts=[])

        # Too many analysts should fail
        many_analysts = [
            Analyst(
                name=f"Dr. Test {i}",
                role="Researcher",
                affiliation="University",
                description="Test description for analyst validation testing",
            )
            for i in range(11)  # Exceeds max_length=10
        ]

        with pytest.raises(ValidationError):
            Perspectives(analysts=many_analysts)

    def test_diverse_roles_validation(self, sample_analysts):
        """Test role diversity validation (warning, not error)."""
        # This should succeed but may log a warning
        perspectives = Perspectives(analysts=sample_analysts)
        assert perspectives is not None


# ============================================================================
# SearchQuery Model Tests
# ============================================================================


class TestSearchQuery:
    """Test suite for SearchQuery model."""

    def test_create_search_query(self):
        """Test creating a search query."""
        query = SearchQuery(search_query="test query")

        assert query.search_query == "test query"

    def test_search_query_none(self):
        """Test search query can be None."""
        query = SearchQuery(search_query=None)

        assert query.search_query is None
        assert query.is_empty()

    def test_search_query_cleaning(self):
        """Test query cleaning and normalization."""
        query = SearchQuery(search_query="  test   query  ")

        # Should be cleaned
        assert query.search_query == "test query"

    def test_get_word_count(self):
        """Test word count calculation."""
        query = SearchQuery(search_query="machine learning research")

        assert query.get_word_count() == 3

        empty_query = SearchQuery(search_query=None)
        assert empty_query.get_word_count() == 0

    def test_is_empty(self):
        """Test empty query detection."""
        empty1 = SearchQuery(search_query=None)
        empty2 = SearchQuery(search_query="")
        empty3 = SearchQuery(search_query="   ")
        valid = SearchQuery(search_query="test")

        assert empty1.is_empty()
        assert empty2.is_empty()
        assert empty3.is_empty()
        assert not valid.is_empty()

    def test_to_dict(self):
        """Test conversion to dictionary for API calls."""
        query = SearchQuery(search_query="test query")
        query_dict = query.to_dict()

        assert "query" in query_dict
        assert query_dict["query"] == "test query"

    def test_query_max_length(self):
        """Test maximum query length."""
        long_query = "word " * 100  # Very long query

        # Should succeed but may be truncated
        query = SearchQuery(search_query=long_query)
        assert query.search_query is not None


# ============================================================================
# Utility Function Tests
# ============================================================================


class TestSchemaUtilities:
    """Test suite for schema utility functions."""

    def test_validate_analyst_diversity_good(self, sample_analysts):
        """Test diversity validation with diverse analysts."""
        is_diverse = validate_analyst_diversity(sample_analysts)

        assert is_diverse is True

    def test_validate_analyst_diversity_poor(self):
        """Test diversity validation with similar analysts."""
        similar_analysts = [
            Analyst(
                name=f"Dr. Test {i}",
                role="Researcher",  # All same role
                affiliation="MIT",  # All same affiliation
                description="Test expert specializing in comprehensive testing",
            )
            for i in range(3)
        ]

        is_diverse = validate_analyst_diversity(similar_analysts)

        # Should be False due to lack of diversity
        assert is_diverse is False

    def test_validate_analyst_diversity_single(self, sample_analyst):
        """Test diversity validation with single analyst."""
        is_diverse = validate_analyst_diversity([sample_analyst])

        # Single analyst always considered diverse
        assert is_diverse is True

    def test_create_analyst_from_dict_valid(self):
        """Test creating analyst from dictionary."""
        data = {
            "name": "Dr. Test",
            "role": "Researcher",
            "affiliation": "University",
            "description": "Test description for analyst validation testing",
        }

        analyst = create_analyst_from_dict(data)

        assert isinstance(analyst, Analyst)
        assert analyst.name == "Dr. Test"

    def test_create_analyst_from_dict_missing_fields(self):
        """Test creating analyst with missing required fields."""
        data = {
            "name": "Dr. Test",
            # Missing role, affiliation, description
        }

        with pytest.raises(ValueError) as exc_info:
            create_analyst_from_dict(data)

        assert "missing required fields" in str(exc_info.value).lower()

    def test_create_analyst_from_dict_invalid_data(self):
        """Test creating analyst with invalid data."""
        data = {
            "name": "A",  # Too short
            "role": "Researcher",
            "affiliation": "University",
            "description": "Short",  # Too short
        }

        with pytest.raises(ValidationError):
            create_analyst_from_dict(data)


# ============================================================================
# Edge Cases and Error Handling
# ============================================================================


class TestSchemaEdgeCases:
    """Test edge cases and error conditions."""

    def test_analyst_special_characters(self):
        """Test analyst with special characters in fields."""
        analyst = Analyst(
            name="Dr. José García-López",
            role="Researcher & Analyst",
            affiliation="University (Main Campus)",
            description="Expert in AI/ML & data science research",
        )

        assert "José" in analyst.name
        assert "&" in analyst.role

    def test_analyst_unicode_support(self):
        """Test Unicode support in analyst fields."""
        analyst = Analyst(
            name="Dr. 陈伟",  # Chinese characters
            role="研究员",
            affiliation="北京大学",
            description="专注于人工智能研究和机器学习应用 - AI research specialist",
        )

        assert analyst.name == "Dr. 陈伟"
        assert len(analyst.description) > 0

    def test_search_query_special_characters(self):
        """Test search query with special characters."""
        query = SearchQuery(search_query="AI/ML & deep-learning")

        assert query.search_query == "AI/ML & deep-learning"

    def test_empty_perspectives_list(self):
        """Test perspectives with empty analyst list."""
        with pytest.raises(ValidationError):
            Perspectives(analysts=[])

    @pytest.mark.parametrize(
        "invalid_name",
        [
            "",
            "A",
            " ",
            "  \n  ",
        ],
    )
    def test_analyst_invalid_names(self, invalid_name):
        """Test various invalid analyst names."""
        with pytest.raises(ValidationError):
            Analyst(
                name=invalid_name,
                role="Researcher",
                affiliation="University",
                description="Valid description here",
            )
