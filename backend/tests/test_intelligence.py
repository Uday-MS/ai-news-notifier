"""Unit tests for Phase 2 — LLM Intelligence Enrichment.

All tests use mocked LLM responses — no live API calls required.

Tests cover:
 1. Provider configuration / missing API key
 2. Successful LLM response
 3. Structured output validation
 4. Malformed LLM output
 5. Timeout handling
 6. Rate limiting
 7. Provider failure
 8. Retry behavior
 9. Idempotency (skip already-enriched)
10. Source provenance preservation
11. Processing status transitions
12. Invalid score/category handling
13. Missing API key behavior
14. Intelligence service batch flow
15. Quality guardrails
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio

from app.ai.intelligence_schema import (
    IntelligenceType,
    LLMIntelligenceOutput,
    validate_intelligence_output,
)
from app.ai.intelligence_prompt import (
    INTELLIGENCE_PROMPT_VERSION,
    SYSTEM_INSTRUCTION,
    build_extraction_prompt,
)
from app.ai.llm_provider import (
    GeminiProvider,
    LLMAuthenticationError,
    LLMProvider,
    LLMProviderError,
    LLMQuotaExhaustedError,
    LLMRateLimitError,
    LLMResponseError,
    LLMTimeoutError,
    get_llm_provider,
    is_quota_exhausted_error,
    parse_retry_after,
)
from app.models.event import CollectedEvent, EventType
from app.models.processed_event import ProcessedEvent, AICategory, ProcessingStatus


# ── Helpers ──────────────────────────────────────────────────────────────


def _make_collected_event(**overrides: Any) -> CollectedEvent:
    """Build a CollectedEvent with sensible defaults."""
    defaults = {
        "id": uuid.uuid4(),
        "title": "Google DeepMind Releases Gemini 2.0 Flash",
        "summary": (
            "Google DeepMind has released Gemini 2.0 Flash, a faster and more "
            "efficient version of their multimodal model. The model offers "
            "improved reasoning at significantly lower latency and cost. "
            "It is now available through the Gemini API."
        ),
        "source": "deepmind-blog",
        "source_url": "https://deepmind.google/blog/gemini-2-flash",
        "published_at": datetime(2025, 7, 1, tzinfo=timezone.utc),
        "event_type": EventType.ANNOUNCEMENT,
        "organization": "Google DeepMind",
        "tags": ["gemini", "ai", "model-release"],
        "extra_metadata": {},
        "collector_id": "rss",
        "content_hash": "test_intel_hash_001",
    }
    defaults.update(overrides)
    return CollectedEvent(**defaults)


def _make_valid_llm_response() -> dict[str, Any]:
    """Return a valid structured LLM response dict."""
    return {
        "concise_summary": (
            "Google DeepMind released Gemini 2.0 Flash, a faster multimodal model "
            "with improved reasoning at lower latency and cost."
        ),
        "why_it_matters": (
            "This release makes advanced multimodal AI more accessible and cost-effective. "
            "Developers can now build faster applications with improved reasoning capabilities. "
            "The lower latency is significant for real-time AI applications."
        ),
        "category": "model_release",
        "subcategory": "multimodal",
        "importance_score": 78,
        "confidence_score": 0.85,
        "relevance_signals": [
            "Major model release from leading AI lab",
            "Cost and latency improvements",
            "Available through public API",
        ],
        "entities": [],
        "technologies": ["Gemini API", "multimodal AI"],
        "organizations": ["Google DeepMind"],
        "models": ["Gemini 2.0 Flash"],
        "keywords": [
            "gemini", "multimodal", "model-release", "efficiency",
            "google-deepmind", "api", "reasoning",
        ],
        "intelligence_type": "model_release",
    }


# ══════════════════════════════════════════════════════════════════════════
# 1. Intelligence Schema Validation
# ══════════════════════════════════════════════════════════════════════════


class TestIntelligenceSchema:
    """Tests for structured output schema validation."""

    def test_valid_output_passes(self):
        data = _make_valid_llm_response()
        result = validate_intelligence_output(data)
        assert isinstance(result, LLMIntelligenceOutput)
        assert result.concise_summary != ""
        assert result.why_it_matters != ""
        assert result.category == "model_release"
        assert result.importance_score == 78
        assert result.confidence_score == 0.85

    def test_clamps_importance_score(self):
        data = _make_valid_llm_response()
        data["importance_score"] = 150
        result = validate_intelligence_output(data)
        assert result.importance_score == 100

    def test_clamps_negative_importance_score(self):
        data = _make_valid_llm_response()
        data["importance_score"] = -10
        result = validate_intelligence_output(data)
        assert result.importance_score == 0

    def test_clamps_confidence_score(self):
        data = _make_valid_llm_response()
        data["confidence_score"] = 2.5
        result = validate_intelligence_output(data)
        assert result.confidence_score == 1.0

    def test_invalid_importance_score_type(self):
        data = _make_valid_llm_response()
        data["importance_score"] = "high"
        result = validate_intelligence_output(data)
        assert result.importance_score == 50  # default

    def test_invalid_confidence_score_type(self):
        data = _make_valid_llm_response()
        data["confidence_score"] = "very confident"
        result = validate_intelligence_output(data)
        assert result.confidence_score == 0.5  # default

    def test_invalid_category_normalised(self):
        data = _make_valid_llm_response()
        data["category"] = "INVALID_CATEGORY"
        result = validate_intelligence_output(data)
        assert result.category == "other"

    def test_invalid_intelligence_type_normalised(self):
        data = _make_valid_llm_response()
        data["intelligence_type"] = "NOT_REAL"
        result = validate_intelligence_output(data)
        assert result.intelligence_type == "other"

    def test_non_list_fields_normalised(self):
        data = _make_valid_llm_response()
        data["entities"] = "not a list"
        data["technologies"] = 42
        result = validate_intelligence_output(data)
        assert result.entities == []
        assert result.technologies == []

    def test_empty_input_uses_defaults(self):
        result = validate_intelligence_output({})
        assert result.concise_summary == ""
        assert result.category == "other"
        assert result.importance_score == 50
        assert result.confidence_score == 0.5

    def test_intelligence_type_enum_values(self):
        """All required intelligence types exist."""
        expected = {
            "news", "research", "model_release", "product_release",
            "funding", "security", "policy", "open_source",
            "opportunity", "company_update", "other",
        }
        actual = {t.value for t in IntelligenceType}
        assert expected == actual


# ══════════════════════════════════════════════════════════════════════════
# 2. Intelligence Prompt
# ══════════════════════════════════════════════════════════════════════════


class TestIntelligencePrompt:
    """Tests for the prompt template."""

    def test_prompt_version_exists(self):
        assert INTELLIGENCE_PROMPT_VERSION == "1.0"

    def test_system_instruction_not_empty(self):
        assert len(SYSTEM_INSTRUCTION) > 50

    def test_system_instruction_contains_rules(self):
        assert "source material" in SYSTEM_INSTRUCTION.lower()
        assert "hallucinate" in SYSTEM_INSTRUCTION.lower()

    def test_build_prompt_includes_all_fields(self):
        prompt = build_extraction_prompt(
            title="Test Title",
            source="test-source",
            source_url="https://example.com/article",
            published_at="2025-07-01T00:00:00Z",
            content="This is the article content about AI developments.",
        )
        assert "Test Title" in prompt
        assert "test-source" in prompt
        assert "https://example.com/article" in prompt
        assert "2025-07-01" in prompt
        assert "article content" in prompt

    def test_build_prompt_truncates_long_content(self):
        long_content = "A" * 5000
        prompt = build_extraction_prompt(
            title="Test",
            source="s",
            source_url="http://x.com",
            published_at="",
            content=long_content,
        )
        assert "[truncated]" in prompt


# ══════════════════════════════════════════════════════════════════════════
# 3. LLM Provider — Configuration & Missing API Key
# ══════════════════════════════════════════════════════════════════════════


class TestLLMProviderConfig:
    """Tests for provider configuration and API key handling."""

    def test_get_llm_provider_returns_none_without_key(self):
        with patch("app.ai.llm_provider.settings") as mock_settings:
            mock_settings.LLM_PROVIDER = "gemini"
            mock_settings.GEMINI_API_KEY = ""
            result = get_llm_provider()
            assert result is None

    def test_get_llm_provider_returns_gemini_with_key(self):
        with patch("app.ai.llm_provider.settings") as mock_settings:
            mock_settings.LLM_PROVIDER = "gemini"
            mock_settings.GEMINI_API_KEY = "test-key-123"
            mock_settings.LLM_MODEL = "gemini-2.0-flash"
            mock_settings.LLM_MAX_RETRIES = 3
            mock_settings.LLM_RETRY_BACKOFF_BASE = 2.0
            mock_settings.LLM_REQUEST_TIMEOUT = 30
            result = get_llm_provider()
            assert isinstance(result, GeminiProvider)

    def test_get_llm_provider_unknown_provider(self):
        with patch("app.ai.llm_provider.settings") as mock_settings:
            mock_settings.LLM_PROVIDER = "unknown_provider"
            mock_settings.GEMINI_API_KEY = "key"
            result = get_llm_provider()
            assert result is None

    def test_gemini_provider_raises_without_key(self):
        provider = GeminiProvider(api_key="", model="gemini-2.0-flash")
        with pytest.raises(LLMAuthenticationError, match="GEMINI_API_KEY"):
            provider._get_client()

    def test_provider_properties(self):
        provider = GeminiProvider(api_key="test", model="gemini-2.0-flash")
        assert provider.provider_name == "gemini"
        assert provider.model_name == "gemini-2.0-flash"


# ══════════════════════════════════════════════════════════════════════════
# 4. LLM Provider — Response Parsing & Errors
# ══════════════════════════════════════════════════════════════════════════


class TestLLMProviderParsing:
    """Tests for JSON parsing and error handling."""

    def test_parse_json_valid(self):
        provider = GeminiProvider(api_key="test", model="test")
        result = provider._parse_json('{"key": "value"}')
        assert result == {"key": "value"}

    def test_parse_json_with_markdown_fence(self):
        provider = GeminiProvider(api_key="test", model="test")
        raw = '```json\n{"key": "value"}\n```'
        result = provider._parse_json(raw)
        assert result == {"key": "value"}

    def test_parse_json_invalid_raises(self):
        provider = GeminiProvider(api_key="test", model="test")
        with pytest.raises(LLMResponseError, match="Failed to parse JSON"):
            provider._parse_json("not valid json at all")

    @pytest.mark.asyncio
    async def test_generate_retries_on_rate_limit(self):
        provider = GeminiProvider(
            api_key="test", model="test",
            max_retries=3, retry_backoff_base=0.01,
        )
        call_count = 0

        async def mock_call(system, user):
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise LLMRateLimitError("rate limited")
            return '{"result": "ok"}'

        provider._call_api = mock_call
        result = await provider.generate("sys", "user")
        assert result == {"result": "ok"}
        assert call_count == 3

    @pytest.mark.asyncio
    async def test_generate_retries_on_timeout(self):
        provider = GeminiProvider(
            api_key="test", model="test",
            max_retries=2, retry_backoff_base=0.01,
        )

        async def mock_call(system, user):
            raise LLMTimeoutError("timed out")

        provider._call_api = mock_call
        with pytest.raises(LLMProviderError, match="All 2 attempts failed"):
            await provider.generate("sys", "user")

    @pytest.mark.asyncio
    async def test_generate_no_retry_on_auth_error(self):
        provider = GeminiProvider(
            api_key="test", model="test",
            max_retries=3, retry_backoff_base=0.01,
        )
        call_count = 0

        async def mock_call(system, user):
            nonlocal call_count
            call_count += 1
            raise LLMAuthenticationError("bad key")

        provider._call_api = mock_call
        with pytest.raises(LLMAuthenticationError):
            await provider.generate("sys", "user")
        assert call_count == 1  # No retries


# ══════════════════════════════════════════════════════════════════════════
# 5. Intelligence Service — Integration Tests with Mocked LLM
# ══════════════════════════════════════════════════════════════════════════


class TestIntelligenceService:
    """Tests for the IntelligenceService using real DB + mocked LLM."""

    @pytest_asyncio.fixture
    async def setup(self, db_session):
        """Set up a collected + processed event pair for testing."""
        from app.repositories.event_repository import EventRepository
        from app.services.pipeline.pipeline_service import PipelineService

        event_repo = EventRepository(db_session)
        event = await event_repo.create(
            title="Google DeepMind Releases Gemini 2.0 Flash",
            summary=(
                "Google DeepMind has released Gemini 2.0 Flash, a faster and more "
                "efficient version of their multimodal model. The model offers "
                "improved reasoning at significantly lower latency and cost."
            ),
            source="deepmind-blog",
            source_url="https://deepmind.google/blog/gemini-2-flash",
            published_at=datetime(2025, 7, 1, tzinfo=timezone.utc),
            event_type=EventType.ANNOUNCEMENT,
            organization="Google DeepMind",
            tags=["gemini", "ai"],
            extra_metadata={},
            collector_id="rss",
            content_hash="intel_test_hash_001",
        )
        await db_session.commit()

        # Process through the pipeline first
        pipeline = PipelineService(db_session)
        processed = await pipeline.process_single(event.id)
        await db_session.commit()

        return event, processed

    def _make_mock_provider(self, response: dict | None = None) -> MagicMock:
        """Create a mock LLM provider that returns a valid response."""
        provider = MagicMock(spec=LLMProvider)
        provider.provider_name = "gemini"
        provider.model_name = "gemini-2.0-flash"
        provider.generate = AsyncMock(
            return_value=response or _make_valid_llm_response()
        )
        return provider

    @pytest.mark.asyncio
    async def test_successful_enrichment(self, db_session, setup):
        """LLM enrichment should populate all intelligence fields."""
        from app.ai.intelligence_service import IntelligenceService

        event, processed = setup
        provider = self._make_mock_provider()
        service = IntelligenceService(db_session, provider)

        result = await service.enrich_single(processed.id)
        await db_session.commit()

        assert result is not None
        assert result.llm_status == "completed"
        assert result.why_it_matters is not None
        assert len(result.why_it_matters) > 10
        assert result.llm_summary is not None
        assert result.llm_category == "model_release"
        assert result.intelligence_type == "model_release"
        assert result.llm_importance_score == 78
        assert result.confidence_score == 0.85
        assert result.llm_provider == "gemini"
        assert result.llm_model == "gemini-2.0-flash"
        assert result.llm_prompt_version == "1.0"
        assert result.llm_processed_at is not None
        assert result.llm_error is None

    @pytest.mark.asyncio
    async def test_idempotency_skip_completed(self, db_session, setup):
        """Already-enriched events should not be re-enriched."""
        from app.ai.intelligence_service import IntelligenceService

        event, processed = setup
        provider = self._make_mock_provider()
        service = IntelligenceService(db_session, provider)

        # First enrichment
        await service.enrich_single(processed.id)
        await db_session.commit()

        # Second enrichment — should skip
        result = await service.enrich_single(processed.id)
        await db_session.commit()

        # generate should only be called once (not twice)
        assert provider.generate.call_count == 1
        assert result.llm_status == "completed"

    @pytest.mark.asyncio
    async def test_force_re_enrichment(self, db_session, setup):
        """Force flag should allow re-enrichment."""
        from app.ai.intelligence_service import IntelligenceService

        event, processed = setup
        provider = self._make_mock_provider()
        service = IntelligenceService(db_session, provider)

        await service.enrich_single(processed.id)
        await db_session.commit()

        await service.enrich_single(processed.id, force=True)
        await db_session.commit()

        assert provider.generate.call_count == 2

    @pytest.mark.asyncio
    async def test_provider_failure_records_error(self, db_session, setup):
        """LLM failure should set status to 'failed' with error message."""
        from app.ai.intelligence_service import IntelligenceService

        event, processed = setup
        provider = self._make_mock_provider()
        provider.generate = AsyncMock(
            side_effect=LLMProviderError("Connection refused")
        )
        service = IntelligenceService(db_session, provider)

        result = await service.enrich_single(processed.id)
        await db_session.commit()

        assert result.llm_status == "failed"
        assert "Connection refused" in result.llm_error
        assert result.llm_attempt_count == 1

    @pytest.mark.asyncio
    async def test_source_provenance_preserved(self, db_session, setup):
        """Enrichment must not alter the source event data."""
        from app.ai.intelligence_service import IntelligenceService

        event, processed = setup
        provider = self._make_mock_provider()
        service = IntelligenceService(db_session, provider)

        result = await service.enrich_single(processed.id)
        await db_session.commit()

        assert result.collected_event_id == event.id
        # Original rule-based fields should still exist
        assert result.cleaned_title is not None
        assert result.ai_category is not None
        assert result.importance_score is not None

    @pytest.mark.asyncio
    async def test_malformed_llm_output_fails(self, db_session, setup):
        """Malformed output (empty summary) should fail gracefully."""
        from app.ai.intelligence_service import IntelligenceService

        event, processed = setup
        provider = self._make_mock_provider(response={
            "concise_summary": "",  # Too short
            "why_it_matters": "",
            "category": "other",
        })
        service = IntelligenceService(db_session, provider)

        result = await service.enrich_single(processed.id)
        await db_session.commit()

        assert result.llm_status == "failed"
        assert "empty" in result.llm_error.lower() or "short" in result.llm_error.lower()

    @pytest.mark.asyncio
    async def test_enrich_pending_batch(self, db_session, setup):
        """Batch enrichment should process pending events."""
        from app.ai.intelligence_service import IntelligenceService

        event, processed = setup
        provider = self._make_mock_provider()
        service = IntelligenceService(db_session, provider)

        summary = await service.enrich_pending(limit=10)
        await db_session.commit()

        assert summary["total"] >= 1
        assert summary["enriched"] >= 1
        assert summary["failed"] == 0

    @pytest.mark.asyncio
    async def test_enrich_pending_skips_completed(self, db_session, setup):
        """Batch enrichment should skip already-completed events."""
        from app.ai.intelligence_service import IntelligenceService

        event, processed = setup
        provider = self._make_mock_provider()
        service = IntelligenceService(db_session, provider)

        # Enrich first
        await service.enrich_pending(limit=10)
        await db_session.commit()

        # Enrich again — should find nothing to do
        summary = await service.enrich_pending(limit=10)
        await db_session.commit()

        assert summary["total"] == 0
        assert summary["enriched"] == 0

    @pytest.mark.asyncio
    async def test_auth_error_stops_batch(self, db_session, setup):
        """Authentication errors should stop the batch immediately."""
        from app.ai.intelligence_service import IntelligenceService

        event, processed = setup
        provider = self._make_mock_provider()
        provider.generate = AsyncMock(
            side_effect=LLMAuthenticationError("Invalid API key")
        )
        service = IntelligenceService(db_session, provider)

        summary = await service.enrich_pending(limit=10)
        await db_session.commit()

        assert summary["failed"] >= 1

    @pytest.mark.asyncio
    async def test_processing_status_transitions(self, db_session, setup):
        """Verify status transitions: pending → processing → completed."""
        from app.ai.intelligence_service import IntelligenceService

        event, processed = setup

        # Initially pending (or None for existing data)
        assert processed.llm_status in ("pending", None)

        provider = self._make_mock_provider()
        service = IntelligenceService(db_session, provider)

        result = await service.enrich_single(processed.id)
        await db_session.commit()

        assert result.llm_status == "completed"

    @pytest.mark.asyncio
    async def test_nonexistent_event_returns_none(self, db_session):
        """Enriching a non-existent event should return None."""
        from app.ai.intelligence_service import IntelligenceService

        provider = self._make_mock_provider()
        service = IntelligenceService(db_session, provider)

        result = await service.enrich_single(uuid.uuid4())
        assert result is None

    @pytest.mark.asyncio
    async def test_attempt_count_increments(self, db_session, setup):
        """Each attempt should increment the attempt counter."""
        from app.ai.intelligence_service import IntelligenceService

        event, processed = setup
        provider = self._make_mock_provider()
        provider.generate = AsyncMock(
            side_effect=LLMProviderError("Fail")
        )
        service = IntelligenceService(db_session, provider)

        # First attempt
        await service.enrich_single(processed.id)
        await db_session.commit()
        assert processed.llm_attempt_count == 1

        # Second attempt (will be picked up since status is "failed")
        await service.enrich_single(processed.id, force=True)
        await db_session.commit()
        assert processed.llm_attempt_count == 2


# ══════════════════════════════════════════════════════════════════════════
# 6. LLM Quota Exhaustion & Circuit Breaker Tests
# ══════════════════════════════════════════════════════════════════════════


class TestLLMQuotaAndFailureHandling:
    """Focused tests for Gemini quota exhaustion, retry prevention, and recovery."""

    def setup_method(self):
        """Reset quota cooldown before each test."""
        LLMProvider.reset_quota_exhaustion()

    def teardown_method(self):
        """Reset quota cooldown after each test."""
        LLMProvider.reset_quota_exhaustion()

    def test_detect_gemini_quota_exhaustion_production_error(self):
        """Must correctly identify the exact Render production error string."""
        production_error = (
            "429 You exceeded your current quota, please check your plan and billing details. "
            "For more information on this error, read: "
            "https://ai.google.dev/gemini-api/docs/troubleshooting/error-codes "
            "Quota metric: generativelanguage.googleapis.com/generate_content_free_tier_requests "
            "Quota: GenerateRequestsPerDayPerProjectPerModel-FreeTier Limit: 20 "
            "Model: gemini-3.6-flash Please retry after 9h39m12s"
        )
        assert is_quota_exhausted_error(Exception(production_error)) is True

    def test_detect_transient_rate_limit_vs_quota_exhaustion(self):
        """Transient rate limits (e.g. 429 Too Many Requests without daily quota) must not be flagged as quota exhaustion."""
        transient_error = "429 Too Many Requests: Rate limit exceeded, please retry in 2 seconds"
        assert is_quota_exhausted_error(Exception(transient_error)) is False

    def test_parse_retry_after_formats(self):
        """Must parse hours, minutes, seconds and raw seconds from retry error strings."""
        assert parse_retry_after("Please retry after 9h39m12s") == 34752.0
        assert parse_retry_after("Please retry after 2h") == 7200.0
        assert parse_retry_after("Please retry after 45s") == 45.0
        assert parse_retry_after("retry_delay: 600") == 600.0
        assert parse_retry_after("No delay info here") is None

    @pytest.mark.asyncio
    async def test_generate_no_retries_on_quota_exhaustion(self):
        """Quota exhaustion must NEVER perform retries — exactly 1 attempt only."""
        provider = GeminiProvider(
            api_key="test-key",
            model="gemini-2.0-flash",
            max_retries=3,
            retry_backoff_base=0.01,
        )
        call_count = 0

        async def mock_call(system, user):
            nonlocal call_count
            call_count += 1
            raise LLMQuotaExhaustedError("Daily quota exceeded", retry_after=3600.0)

        provider._call_api = mock_call

        with pytest.raises(LLMQuotaExhaustedError):
            await provider.generate("sys", "user")

        # Must not retry: exactly 1 call
        assert call_count == 1

    @pytest.mark.asyncio
    async def test_cooldown_blocks_subsequent_calls_without_api_call(self):
        """Active cooldown must reject requests immediately without calling the API."""
        provider = GeminiProvider(
            api_key="test-key",
            model="gemini-2.0-flash",
        )
        provider.record_quota_exhaustion(retry_after=600.0)
        assert provider.is_quota_exhausted() is True

        call_count = 0

        async def mock_call(system, user):
            nonlocal call_count
            call_count += 1
            return '{"ok": true}'

        provider._call_api = mock_call

        with pytest.raises(LLMQuotaExhaustedError, match="in quota cooldown"):
            await provider.generate("sys", "user")

        # Zero API calls made while cooldown is active
        assert call_count == 0

    @pytest.mark.asyncio
    async def test_cooldown_reset_allows_recovery(self):
        """Resetting quota exhaustion must allow requests to proceed normally."""
        provider = GeminiProvider(
            api_key="test-key",
            model="gemini-2.0-flash",
        )
        provider.record_quota_exhaustion(retry_after=600.0)
        assert provider.is_quota_exhausted() is True

        # Recovery / cooldown reset
        provider.reset_quota_exhaustion()
        assert provider.is_quota_exhausted() is False

        provider._call_api = AsyncMock(return_value='{"status": "recovered"}')
        result = await provider.generate("sys", "user")
        assert result == {"status": "recovered"}

    @pytest.mark.asyncio
    async def test_enrich_pending_stops_batch_on_quota_exhaustion(self, db_session):
        """When quota is exhausted on item 1, batch must stop immediately without processing item 2."""
        from app.repositories.event_repository import EventRepository
        from app.services.pipeline.pipeline_service import PipelineService
        from app.ai.intelligence_service import IntelligenceService

        event_repo = EventRepository(db_session)
        pipeline = PipelineService(db_session)

        # Create two events
        e1 = await event_repo.create(
            title="Event 1",
            summary="Summary 1 about AI developments.",
            source="src",
            source_url="https://example.com/1",
            published_at=datetime.now(timezone.utc),
            event_type=EventType.NEWS,
            organization="Org1",
            tags=["ai"],
            extra_metadata={},
            collector_id="rss",
            content_hash="hash_batch_001",
        )
        e2 = await event_repo.create(
            title="Event 2",
            summary="Summary 2 about AI developments.",
            source="src",
            source_url="https://example.com/2",
            published_at=datetime.now(timezone.utc),
            event_type=EventType.NEWS,
            organization="Org2",
            tags=["ai"],
            extra_metadata={},
            collector_id="rss",
            content_hash="hash_batch_002",
        )
        await db_session.commit()

        await pipeline.process_single(e1.id)
        await pipeline.process_single(e2.id)
        await db_session.commit()

        # Mock provider that raises quota exhaustion on first generate call
        generate_calls = 0

        async def mock_generate(system, user):
            nonlocal generate_calls
            generate_calls += 1
            raise LLMQuotaExhaustedError("Daily quota reached: 20 RPD cap", retry_after=3600.0)

        mock_provider = MagicMock(spec=LLMProvider)
        mock_provider.provider_name = "gemini"
        mock_provider.model_name = "gemini-2.0-flash"
        mock_provider.generate = mock_generate

        service = IntelligenceService(db_session, mock_provider)
        summary = await service.enrich_pending(limit=10)
        await db_session.commit()

        # Batch must have stopped immediately after 1 failure
        assert summary["failed"] == 1
        assert summary["enriched"] == 0
        assert generate_calls == 1  # Event 2 was NOT attempted!

    @pytest.mark.asyncio
    async def test_event_preserved_when_quota_exhausted(self, db_session):
        """When LLM enrichment fails due to quota exhaustion, all collected and processed data remains safe."""
        from app.repositories.event_repository import EventRepository
        from app.services.pipeline.pipeline_service import PipelineService
        from app.ai.intelligence_service import IntelligenceService

        event_repo = EventRepository(db_session)
        pipeline = PipelineService(db_session)

        e = await event_repo.create(
            title="Safe Event",
            summary="This summary must not be destroyed by an LLM failure.",
            source="safe-src",
            source_url="https://example.com/safe",
            published_at=datetime.now(timezone.utc),
            event_type=EventType.NEWS,
            organization="SafeOrg",
            tags=["important"],
            extra_metadata={},
            collector_id="rss",
            content_hash="hash_safe_001",
        )
        await db_session.commit()

        processed = await pipeline.process_single(e.id)
        await db_session.commit()

        # Verify initial rule-based processing values
        assert processed.cleaned_title == "Safe Event"
        assert processed.cleaned_summary != ""
        assert processed.ai_category is not None

        mock_provider = MagicMock(spec=LLMProvider)
        mock_provider.provider_name = "gemini"
        mock_provider.model_name = "gemini-2.0-flash"
        mock_provider.generate = AsyncMock(
            side_effect=LLMQuotaExhaustedError("Free tier 20 quota exceeded")
        )

        service = IntelligenceService(db_session, mock_provider)
        with pytest.raises(LLMQuotaExhaustedError):
            await service.enrich_single(processed.id)
        await db_session.commit()

        # Check that the event was safely preserved
        assert processed.collected_event_id == e.id
        assert processed.cleaned_title == "Safe Event"
        assert processed.llm_status == "failed"
        assert "Quota exhausted" in processed.llm_error
        # No fake content was generated
        assert processed.llm_summary is None
        assert processed.why_it_matters is None
