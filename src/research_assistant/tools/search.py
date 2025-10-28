"""Search tools for information retrieval.

This module provides robust search functionality with web search (Tavily) and
Wikipedia search capabilities. Includes retry logic, rate limiting, caching,
and comprehensive error handling.

Example:
    >>> from research_assistant.tools.search import WebSearchTool
    >>> search_tool = WebSearchTool(max_results=3)
    >>> results = search_tool.search("quantum computing applications")
    >>> print(f"Found {len(results)} results")
"""

import hashlib
import logging
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone  # noqa: UP017
from functools import wraps
from typing import Any

from langchain_community.document_loaders import WikipediaLoader
from langchain_openai import ChatOpenAI
from langchain_tavily import TavilySearch

from ..core.schemas import SearchQuery
from ..prompts.interview_prompts import get_search_instructions_as_system_message

# Configure logger
logger = logging.getLogger(__name__)

# Load environment variables from .env if available
from dotenv import load_dotenv
load_dotenv()


class SearchError(Exception):
    """Base exception for search-related errors."""

    pass


class RateLimitError(SearchError):
    """Raised when rate limit is exceeded."""

    pass


class SearchTimeoutError(SearchError):
    """Raised when search times out."""

    pass


# Simple in-memory cache
@dataclass
class CacheEntry:
    """Represents a cached search result."""

    query: str
    results: list[dict[str, Any]]
    timestamp: datetime
    ttl_seconds: int = 3600  # 1 hour default

    def is_expired(self) -> bool:
        """Check if cache entry has expired.

        Returns:
            True if expired, False otherwise.
        """
        age = datetime.now(timezone.utc) - self.timestamp  # noqa: UP017
        return age.total_seconds() > self.ttl_seconds


class SearchCache:
    """Simple in-memory cache for search results."""

    def __init__(self, max_size: int = 100):
        """Initialize search cache.

        Args:
            max_size: Maximum number of entries to cache.
        """
        self._cache: dict[str, CacheEntry] = {}
        self._max_size = max_size
        logger.debug(f"Initialized search cache with max_size={max_size}")

    def _generate_key(self, query: str, search_type: str) -> str:
        """Generate cache key from query and search type.

        Args:
            query: Search query string.
            search_type: Type of search (e.g., 'web', 'wikipedia').

        Returns:
            Cache key string.
        """
        content = f"{search_type}:{query.lower().strip()}"
        return hashlib.sha256(content.encode()).hexdigest()

    def get(self, query: str, search_type: str) -> list[dict[str, Any]] | None:
        """Get cached results if available and not expired.

        Args:
            query: Search query string.
            search_type: Type of search.

        Returns:
            Cached results if available, None otherwise.
        """
        key = self._generate_key(query, search_type)
        entry = self._cache.get(key)

        if entry is None:
            logger.debug(f"Cache miss for query: {query[:50]}")
            return None

        if entry.is_expired():
            logger.debug(f"Cache expired for query: {query[:50]}")
            del self._cache[key]
            return None

        logger.info(f"Cache hit for query: {query[:50]}")
        return entry.results

    def set(
        self, query: str, search_type: str, results: list[dict[str, Any]], ttl_seconds: int = 3600
    ) -> None:
        """Cache search results.

        Args:
            query: Search query string.
            search_type: Type of search.
            results: Search results to cache.
            ttl_seconds: Time-to-live in seconds.
        """
        # Enforce max size by removing oldest entries
        if len(self._cache) >= self._max_size:
            oldest_key = min(self._cache.keys(), key=lambda k: self._cache[k].timestamp)
            del self._cache[oldest_key]
            logger.debug("Cache full, removed oldest entry")

        key = self._generate_key(query, search_type)
        entry = CacheEntry(
            query=query,
            results=results,
            timestamp=datetime.now(timezone.utc),  # noqa: UP017
            ttl_seconds=ttl_seconds,
        )

        self._cache[key] = entry
        logger.debug(f"Cached results for query: {query[:50]}")

    def clear(self) -> None:
        """Clear all cached entries."""
        self._cache.clear()
        logger.info("Search cache cleared")

    def get_stats(self) -> dict[str, Any]:
        """Get cache statistics.

        Returns:
            Dictionary with cache statistics.
        """
        total = len(self._cache)
        expired = sum(1 for entry in self._cache.values() if entry.is_expired())

        return {
            "total_entries": total,
            "expired_entries": expired,
            "active_entries": total - expired,
            "max_size": self._max_size,
        }


def retry_with_backoff(
    max_retries: int = 3,
    initial_delay: float = 1.0,
    backoff_factor: float = 2.0,
    exceptions: tuple = (Exception,),
):
    """Decorator for retrying functions with exponential backoff.

    Args:
        max_retries: Maximum number of retry attempts.
        initial_delay: Initial delay between retries in seconds.
        backoff_factor: Multiplier for delay after each retry.
        exceptions: Tuple of exceptions to catch and retry on.

    Example:
        >>> @retry_with_backoff(max_retries=3)
        ... def unstable_function():
        ...     # May fail occasionally
        ...     pass
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            delay = initial_delay
            last_exception = None

            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e

                    if attempt == max_retries:
                        logger.error(
                            f"{func.__name__} failed after {max_retries} retries: {str(e)}"
                        )
                        raise

                    logger.warning(
                        f"{func.__name__} failed (attempt {attempt + 1}/{max_retries}), "
                        f"retrying in {delay:.1f}s: {str(e)}"
                    )
                    time.sleep(delay)
                    delay *= backoff_factor

            raise last_exception

        return wrapper

    return decorator


@dataclass
class RateLimiter:
    """Simple token bucket rate limiter."""

    max_requests: int = 10
    time_window: int = 60  # seconds
    _requests: list[datetime] = field(default_factory=list)

    def check_and_wait(self) -> None:
        """Check rate limit and wait if necessary.

        Raises:
            RateLimitError: If rate limit would be exceeded even after waiting.
        """
        now = datetime.now(timezone.utc)  # noqa: UP017
        cutoff = now - timedelta(seconds=self.time_window)

        # Remove old requests outside the time window
        self._requests = [req for req in self._requests if req > cutoff]

        if len(self._requests) >= self.max_requests:
            oldest_request = self._requests[0]
            wait_time = (oldest_request + timedelta(seconds=self.time_window) - now).total_seconds()

            if wait_time > 0:
                logger.warning(f"Rate limit reached, waiting {wait_time:.1f}s")
                time.sleep(wait_time)
                # Re-check after waiting
                return self.check_and_wait()

        # Record this request
        self._requests.append(now)
        logger.debug(f"Rate limit check: {len(self._requests)}/{self.max_requests} requests")
        return None


class WebSearchTool:
    """Web search tool using Tavily with retry logic and caching.

    Attributes:
        max_results: Maximum number of search results to return.
        cache: Search cache instance.
        rate_limiter: Rate limiter instance.

    Example:
        >>> tool = WebSearchTool(max_results=5)
        >>> results = tool.search("artificial intelligence")
        >>> for result in results:
        ...     print(result['url'])
    """

    def __init__(
        self,
        max_results: int = 3,
        use_cache: bool = True,
        cache_ttl: int = 3600,
        rate_limit_requests: int = 10,
        rate_limit_window: int = 60,
        timeout: int = 30,
    ):
        """Initialize web search tool.

        Args:
            max_results: Maximum search results to return.
            use_cache: Whether to use caching.
            cache_ttl: Cache time-to-live in seconds.
            rate_limit_requests: Max requests per time window.
            rate_limit_window: Time window in seconds.
            timeout: Search timeout in seconds.
        """
        self.max_results = max_results
        self.use_cache = use_cache
        self.cache_ttl = cache_ttl
        self.timeout = timeout

        # Initialize cache
        self.cache = SearchCache() if use_cache else None

        # Initialize rate limiter
        self.rate_limiter = RateLimiter(
            max_requests=rate_limit_requests, time_window=rate_limit_window
        )

        # Initialize Tavily search
        self._tavily = TavilySearch(max_results=max_results)

        logger.info(
            f"Initialized WebSearchTool: max_results={max_results}, "
            f"cache={use_cache}, rate_limit={rate_limit_requests}/{rate_limit_window}s"
        )

    @retry_with_backoff(max_retries=3, exceptions=(Exception,))
    def search(self, query: str) -> list[dict[str, Any]]:
        """Execute web search with retry and caching.

        Args:
            query: Search query string.

        Returns:
            List of search result dictionaries with 'url' and 'content' keys.

        Raises:
            SearchError: If search fails after retries.
            RateLimitError: If rate limit is exceeded.

        Example:
            >>> results = tool.search("machine learning")
            >>> print(results[0]['url'])
        """
        if not query or not query.strip():
            raise ValueError("Search query cannot be empty")

        query = query.strip()
        logger.info(f"Web search for: {query[:100]}")

        # Check cache first
        if self.cache:
            cached = self.cache.get(query, "web")
            if cached is not None:
                return cached

        # Check rate limit
        try:
            self.rate_limiter.check_and_wait()
        except Exception as e:
            raise RateLimitError(f"Rate limit exceeded: {str(e)}") from e

        # Execute search
        try:
            start_time = time.time()

            # Tavily returns results or dict with 'results' key
            data = self._tavily.invoke({"query": query})
            search_results = data.get("results", data) if isinstance(data, dict) else data

            elapsed = time.time() - start_time
            logger.debug(f"Search completed in {elapsed:.2f}s")

            if not isinstance(search_results, list):
                raise SearchError(f"Unexpected search result type: {type(search_results)}")

            logger.info(f"Found {len(search_results)} results")

            # Cache results
            if self.cache:
                self.cache.set(query, "web", search_results, self.cache_ttl)

            return search_results

        except Exception as e:
            logger.error(f"Web search failed for query '{query[:50]}': {str(e)}")
            raise SearchError(f"Web search failed: {str(e)}") from e

    def format_results(self, results: list[dict[str, Any]]) -> str:
        """Format search results for LLM context.

        Args:
            results: List of search result dictionaries.

        Returns:
            Formatted string with document tags.

        Example:
            >>> formatted = tool.format_results(results)
            >>> print(formatted[:100])
        """
        formatted_docs = []

        for doc in results:
            url = doc.get("url", "unknown")
            content = doc.get("content", "")

            formatted_docs.append(f'<Document href="{url}"/>\n{content}\n</Document>')

        return "\n\n---\n\n".join(formatted_docs)


class WikipediaSearchTool:
    """Wikipedia search tool with retry logic and caching.

    Attributes:
        load_max_docs: Maximum number of Wikipedia documents to load.
        cache: Search cache instance.
        rate_limiter: Rate limiter instance.

    Example:
        >>> tool = WikipediaSearchTool(load_max_docs=2)
        >>> results = tool.search("quantum computing")
        >>> print(results[0].page_content[:100])
    """

    def __init__(
        self,
        load_max_docs: int = 2,
        use_cache: bool = True,
        cache_ttl: int = 7200,  # 2 hours for Wikipedia (changes less frequently)
        rate_limit_requests: int = 10,
        rate_limit_window: int = 60,
    ):
        """Initialize Wikipedia search tool.

        Args:
            load_max_docs: Maximum documents to load.
            use_cache: Whether to use caching.
            cache_ttl: Cache time-to-live in seconds.
            rate_limit_requests: Max requests per time window.
            rate_limit_window: Time window in seconds.
        """
        self.load_max_docs = load_max_docs
        self.use_cache = use_cache
        self.cache_ttl = cache_ttl

        # Initialize cache
        self.cache = SearchCache() if use_cache else None

        # Initialize rate limiter
        self.rate_limiter = RateLimiter(
            max_requests=rate_limit_requests, time_window=rate_limit_window
        )

        logger.info(
            f"Initialized WikipediaSearchTool: load_max_docs={load_max_docs}, " f"cache={use_cache}"
        )

    @retry_with_backoff(max_retries=3, exceptions=(Exception,))
    def search(self, query: str) -> list[Any]:
        """Execute Wikipedia search with retry and caching.

        Args:
            query: Search query string.

        Returns:
            List of LangChain Document objects.

        Raises:
            SearchError: If search fails after retries.

        Example:
            >>> docs = tool.search("artificial intelligence")
            >>> print(docs[0].metadata['source'])
        """
        if not query or not query.strip():
            raise ValueError("Search query cannot be empty")

        query = query.strip()
        logger.info(f"Wikipedia search for: {query[:100]}")

        # Check cache first (convert documents to dicts for caching)
        if self.cache:
            cached = self.cache.get(query, "wikipedia")
            if cached is not None:
                # Reconstruct documents from cached data
                from langchain_core.documents import Document

                return [
                    Document(page_content=item["page_content"], metadata=item["metadata"])
                    for item in cached
                ]

        # Check rate limit
        try:
            self.rate_limiter.check_and_wait()
        except Exception as e:
            raise RateLimitError(f"Rate limit exceeded: {str(e)}") from e

        # Execute search
        try:
            start_time = time.time()

            loader = WikipediaLoader(query=query, load_max_docs=self.load_max_docs)
            documents = loader.load()

            elapsed = time.time() - start_time
            logger.debug(f"Wikipedia search completed in {elapsed:.2f}s")
            logger.info(f"Loaded {len(documents)} Wikipedia documents")

            # Cache results (convert to dicts)
            if self.cache and documents:
                cache_data = [
                    {"page_content": doc.page_content, "metadata": doc.metadata}
                    for doc in documents
                ]
                self.cache.set(query, "wikipedia", cache_data, self.cache_ttl)

            return documents

        except Exception as e:
            logger.error(f"Wikipedia search failed for query '{query[:50]}': {str(e)}")
            raise SearchError(f"Wikipedia search failed: {str(e)}") from e

    def format_results(self, documents: list[Any]) -> str:
        """Format Wikipedia documents for LLM context.

        Args:
            documents: List of LangChain Document objects.

        Returns:
            Formatted string with document tags.

        Example:
            >>> formatted = tool.format_results(docs)
            >>> print(formatted[:100])
        """
        formatted_docs = []

        for doc in documents:
            source = doc.metadata.get("source", "unknown")
            page = doc.metadata.get("page", "")
            page_attr = f' page="{page}"' if page else ""

            formatted_docs.append(
                f'<Document source="{source}"{page_attr}/>\n' f"{doc.page_content}\n</Document>"
            )

        return "\n\n---\n\n".join(formatted_docs)


class SearchQueryGenerator:
    """Generates optimized search queries from conversation context.

    Example:
        >>> generator = SearchQueryGenerator()
        >>> query = generator.generate_from_messages(messages)
        >>> print(query.search_query)
    """

    def __init__(self, llm: ChatOpenAI | None = None):
        """Initialize search query generator.

        Args:
            llm: Optional LLM instance for query generation.
        """
        self.llm = llm or ChatOpenAI(model="gpt-4o", temperature=0)
        logger.debug("Initialized SearchQueryGenerator")

    def generate_from_messages(self, messages: list[Any], detailed: bool = False) -> SearchQuery:
        """Generate a search query from conversation messages.

        Args:
            messages: List of conversation messages.
            detailed: If True, use detailed instructions.

        Returns:
            SearchQuery instance with optimized query.

        Raises:
            SearchError: If query generation fails.

        Example:
            >>> query = generator.generate_from_messages([msg1, msg2])
            >>> print(query.search_query)
        """
        logger.info("Generating search query from conversation")

        if not messages:
            raise ValueError("No messages provided for query generation")

        # Get search instructions
        search_instructions = get_search_instructions_as_system_message(detailed=detailed)

        # Enforce structured output
        structured_llm = self.llm.with_structured_output(SearchQuery)

        try:
            # Generate query
            search_query = structured_llm.invoke([search_instructions] + messages)

            if not isinstance(search_query, SearchQuery):
                raise SearchError(f"Expected SearchQuery, got {type(search_query)}")

            logger.info(f"Generated search query: {search_query.search_query}")
            return search_query

        except Exception as e:
            logger.error(f"Failed to generate search query: {str(e)}")
            raise SearchError(f"Query generation failed: {str(e)}") from e


# Factory function for creating search tools


def create_search_tools(
    web_max_results: int = 3, wiki_max_docs: int = 2, use_cache: bool = True, rate_limit: int = 10
) -> dict[str, Any]:
    """Factory function to create configured search tools.

    Args:
        web_max_results: Max results for web search.
        wiki_max_docs: Max documents for Wikipedia search.
        use_cache: Whether to enable caching.
        rate_limit: Max requests per minute.

    Returns:
        Dictionary with 'web', 'wikipedia', and 'query_generator' tools.

    Example:
        >>> tools = create_search_tools(web_max_results=5)
        >>> web_tool = tools['web']
        >>> results = web_tool.search("AI research")
    """
    logger.info("Creating search tools")

    return {
        "web": WebSearchTool(
            max_results=web_max_results,
            use_cache=use_cache,
            rate_limit_requests=rate_limit,
            rate_limit_window=60,
        ),
        "wikipedia": WikipediaSearchTool(
            load_max_docs=wiki_max_docs,
            use_cache=use_cache,
            rate_limit_requests=rate_limit,
            rate_limit_window=60,
        ),
        "query_generator": SearchQueryGenerator(),
    }
