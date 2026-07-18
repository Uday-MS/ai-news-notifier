"""Unit tests for the AI Processing Pipeline (Sprint 4).

Tests cover:
- Content cleaning service
- Classification service
- Tag extraction service
- Entity extraction service
- Importance scoring service
- Summary service (rule-based)
- Quality validation service
- Pipeline orchestrator (single + batch)
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models.event import CollectedEvent, EventType
from app.models.processed_event import AICategory, ProcessingStatus
from app.models.processing_log import StageStatus
from app.services.pipeline.cleaning_service import CleaningService
from app.services.pipeline.classification_service import ClassificationService
from app.services.pipeline.entity_service import EntityService
from app.services.pipeline.importance_service import ImportanceService
from app.services.pipeline.quality_service import QualityService
from app.services.pipeline.summary_service import RuleBasedSummarizer
from app.services.pipeline.tag_service import TagService


# ── Helpers ──────────────────────────────────────────────────────────────


def _make_collected_event(**overrides: Any) -> CollectedEvent:
    """Build a CollectedEvent with sensible defaults for testing."""
    defaults = {
        "id": uuid.uuid4(),
        "title": "OpenAI Launches GPT-5 with Multimodal Support",
        "summary": (
            "OpenAI has released GPT-5, its latest foundation model with "
            "improved reasoning, multimodal input support, and faster inference. "
            "The model is now available through the API and ChatGPT. "
            "This represents a major leap in language model capabilities."
        ),
        "source": "openai-blog",
        "source_url": "https://openai.com/blog/gpt-5-launch",
        "published_at": datetime(2025, 6, 1, tzinfo=timezone.utc),
        "event_type": EventType.ANNOUNCEMENT,
        "organization": "OpenAI",
        "tags": ["gpt-5", "ai", "launch"],
        "extra_metadata": {"stars": 5000},
        "collector_id": "rss",
        "content_hash": "abc123",
    }
    defaults.update(overrides)
    event = CollectedEvent(**defaults)
    return event


# ══════════════════════════════════════════════════════════════════════════
# Stage 1: Cleaning Service
# ══════════════════════════════════════════════════════════════════════════


class TestCleaningService:
    """Tests for the content cleaning pipeline."""

    def setup_method(self):
        self.svc = CleaningService()

    def test_clean_removes_html_tags(self):
        result = self.svc.clean(
            title="Test <b>Title</b>",
            summary="<p>Some <em>content</em> here with <a href='#'>links</a>.</p>",
        )
        assert "<b>" not in result.title
        assert "<p>" not in result.summary
        assert "<em>" not in result.summary
        assert "content" in result.summary

    def test_clean_normalizes_whitespace(self):
        result = self.svc.clean(
            title="  Multiple   spaces   here  ",
            summary="Content  with   many    spaces  and\n\n\n\nmany newlines here for testing.",
        )
        assert "  " not in result.title
        assert "\n\n\n" not in result.summary

    def test_clean_decodes_html_entities(self):
        result = self.svc.clean(
            title="Test &amp; Title &lt;here&gt;",
            summary="Content with &quot;entities&quot; and more text for length.",
        )
        assert "&amp;" not in result.title
        assert "&" in result.title

    def test_clean_url_removes_tracking(self):
        url = "https://example.com/article?utm_source=twitter&utm_medium=social&id=123"
        cleaned = self.svc.clean_url(url)
        assert "utm_source" not in cleaned
        assert "utm_medium" not in cleaned
        assert "id=123" in cleaned

    def test_clean_url_preserves_non_tracking_params(self):
        url = "https://example.com/search?q=ai+news&page=2"
        cleaned = self.svc.clean_url(url)
        assert "q=ai+news" in cleaned or "q=ai%2Bnews" in cleaned or "q=ai" in cleaned
        assert "page=2" in cleaned

    def test_clean_validates_minimum_length(self):
        result = self.svc.clean(title="OK Title", summary="Short")
        assert result.is_valid is False
        assert "minimum length" in result.validation_reason.lower()

    def test_clean_validates_title_length(self):
        result = self.svc.clean(title="AB", summary="This is a sufficiently long summary for testing.")
        assert result.is_valid is False
        assert "title" in result.validation_reason.lower()

    def test_clean_valid_content(self):
        result = self.svc.clean(
            title="A Valid Title",
            summary="This is a sufficiently long summary for validation testing.",
        )
        assert result.is_valid is True

    def test_clean_markdown_links(self):
        result = self.svc.clean(
            title="Test Title Here",
            summary="Check [this link](https://example.com) for more info and details.",
        )
        assert "this link" in result.summary
        assert "](https://" not in result.summary

    def test_clean_markdown_images(self):
        result = self.svc.clean(
            title="Test Title Here",
            summary="Here is an image ![alt text](https://img.com/a.png) in content that is long enough.",
        )
        assert "![" not in result.summary

    def test_clean_empty_input(self):
        result = self.svc.clean(title="", summary="")
        assert result.is_valid is False


# ══════════════════════════════════════════════════════════════════════════
# Stage 2: Classification Service
# ══════════════════════════════════════════════════════════════════════════


class TestClassificationService:
    """Tests for keyword-based event classification."""

    def setup_method(self):
        self.svc = ClassificationService()

    def test_classify_ai_model(self):
        result = self.svc.classify(
            title="GPT-5 Released by OpenAI",
            summary="A new language model with improved capabilities.",
        )
        assert result == AICategory.AI_MODEL

    def test_classify_security(self):
        result = self.svc.classify(
            title="Critical Vulnerability Found in AI Framework",
            summary="A zero-day exploit was discovered in a popular ML library.",
        )
        assert result == AICategory.SECURITY

    def test_classify_funding(self):
        result = self.svc.classify(
            title="AI Startup Raises $100M Series B",
            summary="The company completed its series b funding round.",
        )
        assert result == AICategory.FUNDING

    def test_classify_research(self):
        result = self.svc.classify(
            title="New Attention Mechanism for Transformers",
            summary="Researchers propose a novel state-of-the-art approach using reinforcement learning.",
        )
        assert result == AICategory.AI_RESEARCH

    def test_classify_open_source(self):
        result = self.svc.classify(
            title="New Open Source LLM Framework",
            summary="Available on github.com under the MIT license.",
        )
        assert result == AICategory.OPEN_SOURCE

    def test_classify_hackathon(self):
        result = self.svc.classify(
            title="Global AI Hackathon 2025",
            summary="Join the biggest hackathon of the year.",
        )
        assert result == AICategory.HACKATHON

    def test_classify_internship(self):
        result = self.svc.classify(
            title="Summer AI Internship at Google",
            summary="Apply for the internship program now.",
        )
        assert result == AICategory.INTERNSHIP

    def test_classify_product_release(self):
        result = self.svc.classify(
            title="Company X Introduces New AI SDK",
            summary="The SDK introduces powerful integration features.",
        )
        assert result == AICategory.PRODUCT_RELEASE

    def test_classify_other_fallback(self):
        result = self.svc.classify(
            title="Weather Update",
            summary="It will be sunny tomorrow.",
        )
        assert result == AICategory.OTHER

    def test_classify_uses_tags(self):
        result = self.svc.classify(
            title="New Project Release",
            summary="Check out this project.",
            tags=["hackathon", "ai"],
        )
        assert result == AICategory.HACKATHON

    def test_classify_uses_organization(self):
        result = self.svc.classify(
            title="New Program Announced",
            summary="Applications open for students.",
            organization="Y Combinator",
        )
        assert result == AICategory.STARTUP


# ══════════════════════════════════════════════════════════════════════════
# Stage 3: Tag Extraction Service
# ══════════════════════════════════════════════════════════════════════════


class TestTagService:
    """Tests for tag extraction and normalization."""

    def setup_method(self):
        self.svc = TagService()

    def test_extract_known_tags(self):
        tags = self.svc.extract_tags(
            title="OpenAI Releases GPT-4 Update",
            summary="The latest PyTorch-based model uses transformer architecture.",
        )
        assert "openai" in tags
        assert "gpt-4" in tags
        assert "pytorch" in tags
        assert "transformer" in tags

    def test_extract_merges_existing_tags(self):
        tags = self.svc.extract_tags(
            title="Some Event",
            summary="Description here.",
            existing_tags=["custom-tag", "another"],
        )
        assert "custom-tag" in tags
        assert "another" in tags

    def test_extract_from_metadata_repo(self):
        tags = self.svc.extract_tags(
            title="Some Event",
            summary="Description here.",
            extra_metadata={"repository": "openai/gpt-toolkit"},
        )
        assert "openai" in tags
        assert "gpt-toolkit" in tags

    def test_extract_normalizes_to_lowercase(self):
        tags = self.svc.extract_tags(
            title="PYTORCH Model Release",
            summary="Using TensorFlow framework.",
        )
        for tag in tags:
            assert tag == tag.lower()

    def test_extract_deduplicates(self):
        tags = self.svc.extract_tags(
            title="PyTorch PyTorch PyTorch",
            summary="Using PyTorch for deep learning.",
        )
        assert tags.count("pytorch") == 1

    def test_extract_adds_organization_tag(self):
        tags = self.svc.extract_tags(
            title="Event Title",
            summary="Event description.",
            organization="DeepMind",
        )
        assert "deepmind" in tags

    def test_extract_filters_short_tags(self):
        tags = self.svc.extract_tags(
            title="Event Title",
            summary="Event description.",
            existing_tags=["a", ""],
        )
        for tag in tags:
            assert len(tag) >= 2


# ══════════════════════════════════════════════════════════════════════════
# Stage 4: Entity Extraction Service
# ══════════════════════════════════════════════════════════════════════════


class TestEntityService:
    """Tests for pattern-based entity extraction."""

    def setup_method(self):
        self.svc = EntityService()

    def test_extract_organizations(self):
        entities = self.svc.extract_entities(
            title="OpenAI and Google announce partnership",
            summary="Microsoft joins the collaboration.",
        )
        assert "OpenAI" in entities["organizations"]
        assert "Google" in entities["organizations"]
        assert "Microsoft" in entities["organizations"]

    def test_extract_models(self):
        entities = self.svc.extract_entities(
            title="GPT-4 vs Claude comparison",
            summary="Both models show impressive results.",
        )
        assert "GPT-4" in entities["models"]
        assert "Claude" in entities["models"]

    def test_extract_frameworks(self):
        entities = self.svc.extract_entities(
            title="Building with PyTorch and JAX",
            summary="Using the Transformers library for inference.",
        )
        assert "PyTorch" in entities["frameworks"]
        assert "JAX" in entities["frameworks"]
        assert "Transformers" in entities["frameworks"]

    def test_extract_languages(self):
        entities = self.svc.extract_entities(
            title="Python and Rust for AI Development",
            summary="Both languages are gaining popularity.",
        )
        assert "Python" in entities["languages"]
        assert "Rust" in entities["languages"]

    def test_extract_repositories(self):
        entities = self.svc.extract_entities(
            title="Check out the new tool",
            summary="Available at https://github.com/openai/whisper for download.",
        )
        assert "openai/whisper" in entities["repositories"]

    def test_extract_products(self):
        entities = self.svc.extract_entities(
            title="ChatGPT Gets New Features",
            summary="GitHub Copilot integration is now available.",
        )
        assert "ChatGPT" in entities["products"]
        assert "GitHub Copilot" in entities["products"]

    def test_extract_people(self):
        entities = self.svc.extract_entities(
            title="CEO Sam Altman announces new initiative",
            summary="Co-founder John Smith joins the board.",
        )
        assert "Sam Altman" in entities["people"]

    def test_adds_organization_field(self):
        entities = self.svc.extract_entities(
            title="Test event",
            summary="Some description.",
            organization="CustomOrg",
        )
        assert "CustomOrg" in entities["organizations"]

    def test_empty_input(self):
        entities = self.svc.extract_entities(title="", summary="")
        assert isinstance(entities, dict)
        assert all(isinstance(v, list) for v in entities.values())


# ══════════════════════════════════════════════════════════════════════════
# Stage 5: Importance Scoring Service
# ══════════════════════════════════════════════════════════════════════════


class TestImportanceService:
    """Tests for deterministic importance scoring."""

    def setup_method(self):
        self.svc = ImportanceService()

    def test_score_range(self):
        score, reason = self.svc.score(
            title="Test event",
            summary="Test summary.",
            source="test",
            source_url="https://example.com",
            organization="TestOrg",
            ai_category=AICategory.OTHER,
        )
        assert 0 <= score <= 100
        assert isinstance(reason, str)

    def test_official_source_bonus(self):
        score_official, _ = self.svc.score(
            title="Test",
            summary="Test.",
            source="openai",
            source_url="https://openai.com/blog/test",
            organization="OpenAI",
            ai_category=AICategory.AI_MODEL,
        )
        score_other, _ = self.svc.score(
            title="Test",
            summary="Test.",
            source="random-blog",
            source_url="https://random-blog.com/test",
            organization="RandomBlog",
            ai_category=AICategory.AI_MODEL,
        )
        assert score_official > score_other

    def test_verified_org_bonus(self):
        score, reason = self.svc.score(
            title="Test",
            summary="Test.",
            source="test",
            source_url="https://example.com",
            organization="Google",
            ai_category=AICategory.OTHER,
        )
        assert "Verified organization" in reason

    def test_github_stars_bonus(self):
        score, reason = self.svc.score(
            title="Test",
            summary="Test.",
            source="test",
            source_url="https://example.com",
            organization="TestOrg",
            ai_category=AICategory.OPEN_SOURCE,
            extra_metadata={"stars": 15000},
        )
        assert "GitHub stars" in reason

    def test_breaking_release_bonus(self):
        score, reason = self.svc.score(
            title="Major Release: New AI Platform",
            summary="This is a major release of the platform.",
            source="test",
            source_url="https://example.com",
            organization="TestOrg",
            ai_category=AICategory.PRODUCT_RELEASE,
        )
        assert "Breaking release" in reason

    def test_security_urgency_bonus(self):
        score, reason = self.svc.score(
            title="Critical Vulnerability in AI Framework",
            summary="An actively exploited zero-day was found.",
            source="test",
            source_url="https://example.com",
            organization="TestOrg",
            ai_category=AICategory.SECURITY,
        )
        assert "Urgent security" in reason

    def test_category_base_scores_differ(self):
        score_security, _ = self.svc.score(
            title="Test", summary="Test.", source="t",
            source_url="https://x.com", organization="X",
            ai_category=AICategory.SECURITY,
        )
        score_other, _ = self.svc.score(
            title="Test", summary="Test.", source="t",
            source_url="https://x.com", organization="X",
            ai_category=AICategory.OTHER,
        )
        assert score_security > score_other


# ══════════════════════════════════════════════════════════════════════════
# Stage 6: Summary Service
# ══════════════════════════════════════════════════════════════════════════


class TestSummaryService:
    """Tests for the rule-based summarizer."""

    def setup_method(self):
        self.svc = RuleBasedSummarizer()

    @pytest.mark.asyncio
    async def test_summarize_returns_string(self):
        result = await self.svc.summarize(
            title="Test Event",
            content="This is a detailed description of the event. It contains multiple sentences. Each provides important context. The conclusion is clear.",
        )
        assert isinstance(result, str)
        assert len(result) > 0

    @pytest.mark.asyncio
    async def test_summarize_respects_max_length(self):
        long_content = ". ".join([f"Sentence number {i} with some additional content" for i in range(50)])
        result = await self.svc.summarize(title="Long Content", content=long_content)
        assert len(result) <= self.svc.MAX_SUMMARY_LENGTH + 50  # Allow context prefix

    @pytest.mark.asyncio
    async def test_summarize_empty_content_fallback(self):
        result = await self.svc.summarize(
            title="Test Event",
            content="",
            organization="TestOrg",
            category="ai_model",
        )
        assert "Test Event" in result
        assert "TestOrg" in result

    @pytest.mark.asyncio
    async def test_summarize_short_content_kept(self):
        result = await self.svc.summarize(
            title="Test",
            content="This is already a concise description of the event.",
        )
        assert "concise description" in result

    @pytest.mark.asyncio
    async def test_summarize_inherits_base(self):
        from app.services.pipeline.summary_service import BaseSummarizer
        assert isinstance(self.svc, BaseSummarizer)


# ══════════════════════════════════════════════════════════════════════════
# Stage 7: Quality Validation Service
# ══════════════════════════════════════════════════════════════════════════


class TestQualityService:
    """Tests for quality validation and status determination."""

    def setup_method(self):
        self.svc = QualityService()

    def test_ready_status(self):
        result = self.svc.validate(
            cleaned_title="Valid Title",
            cleaned_summary="Valid summary content here.",
            ai_category=AICategory.AI_MODEL,
            ai_tags=["ai", "model"],
            entities={"organizations": ["OpenAI"]},
            importance_score=50,
            importance_reason="Good score.",
            ai_summary="A concise summary.",
        )
        assert result.status == ProcessingStatus.READY

    def test_failed_status_missing_title(self):
        result = self.svc.validate(
            cleaned_title="",
            cleaned_summary="Valid summary.",
            ai_category=AICategory.OTHER,
            ai_tags=[],
            entities={},
            importance_score=10,
            importance_reason="Low.",
            ai_summary="Summary.",
        )
        assert result.status == ProcessingStatus.FAILED

    def test_failed_status_missing_summary(self):
        result = self.svc.validate(
            cleaned_title="Valid Title",
            cleaned_summary="",
            ai_category=AICategory.OTHER,
            ai_tags=[],
            entities={},
            importance_score=10,
            importance_reason="Low.",
            ai_summary="Summary.",
        )
        assert result.status == ProcessingStatus.FAILED

    def test_failed_status_cleaning_failure(self):
        result = self.svc.validate(
            cleaned_title="Valid Title",
            cleaned_summary="Valid summary.",
            ai_category=AICategory.OTHER,
            ai_tags=[],
            entities={},
            importance_score=10,
            importance_reason="Low.",
            ai_summary="Summary.",
            stage_failures=["cleaning"],
        )
        assert result.status == ProcessingStatus.FAILED

    def test_partial_status_missing_classification(self):
        result = self.svc.validate(
            cleaned_title="Valid Title",
            cleaned_summary="Valid summary.",
            ai_category=None,
            ai_tags=["tag"],
            entities={"organizations": ["Org"]},
            importance_score=50,
            importance_reason="Good.",
            ai_summary="Summary.",
        )
        assert result.status == ProcessingStatus.PARTIAL

    def test_partial_status_missing_summary(self):
        result = self.svc.validate(
            cleaned_title="Valid Title",
            cleaned_summary="Valid summary.",
            ai_category=AICategory.OTHER,
            ai_tags=["tag"],
            entities={"organizations": ["Org"]},
            importance_score=50,
            importance_reason="Good.",
            ai_summary="",
        )
        assert result.status == ProcessingStatus.PARTIAL

    def test_issues_list_populated(self):
        result = self.svc.validate(
            cleaned_title="Valid Title",
            cleaned_summary="Valid summary.",
            ai_category=AICategory.OTHER,
            ai_tags=[],
            entities={},
            importance_score=50,
            importance_reason="",
            ai_summary="Summary.",
        )
        # Should note missing tags, entities, importance reason
        assert len(result.issues) > 0


# ══════════════════════════════════════════════════════════════════════════
# Pipeline Orchestrator (Integration-like tests with mocked DB)
# ══════════════════════════════════════════════════════════════════════════


class TestPipelineIntegration:
    """Integration-like tests for the pipeline orchestrator using real DB."""

    @pytest.mark.asyncio
    async def test_process_single_event(self, db_session):
        """Process a single event through the full pipeline."""
        from app.repositories.event_repository import EventRepository
        from app.services.pipeline.pipeline_service import PipelineService

        # Create a collected event
        event_repo = EventRepository(db_session)
        event = await event_repo.create(
            title="OpenAI Launches GPT-5 with Multimodal Support",
            summary=(
                "OpenAI has released GPT-5, its latest foundation model with "
                "improved reasoning, multimodal input support, and faster inference. "
                "The model is now available through the API and ChatGPT. "
                "This represents a major leap in language model capabilities."
            ),
            source="openai-blog",
            source_url="https://openai.com/blog/gpt-5-launch",
            published_at=datetime(2025, 6, 1, tzinfo=timezone.utc),
            event_type=EventType.ANNOUNCEMENT,
            organization="OpenAI",
            tags=["gpt-5", "ai", "launch"],
            extra_metadata={"stars": 5000},
            collector_id="rss",
            content_hash="test_hash_001",
        )
        await db_session.commit()

        # Run the pipeline
        service = PipelineService(db_session)
        processed = await service.process_single(event.id)
        await db_session.commit()

        # Verify output
        assert processed is not None
        assert processed.collected_event_id == event.id
        assert processed.cleaned_title  # Non-empty
        assert processed.cleaned_summary  # Non-empty
        assert processed.ai_category in AICategory
        assert isinstance(processed.ai_tags, list)
        assert isinstance(processed.entities, dict)
        assert 0 <= processed.importance_score <= 100
        assert processed.importance_reason  # Non-empty
        assert processed.ai_summary  # Non-empty
        assert processed.processing_status in ProcessingStatus
        assert processed.processed_at is not None

    @pytest.mark.asyncio
    async def test_process_all_unprocessed(self, db_session):
        """Process multiple unprocessed events."""
        from app.repositories.event_repository import EventRepository
        from app.services.pipeline.pipeline_service import PipelineService

        event_repo = EventRepository(db_session)

        # Create two collected events
        await event_repo.create(
            title="Event One: Security Vulnerability Found",
            summary="A critical vulnerability was discovered in a popular machine learning framework that could be exploited.",
            source="security-blog",
            source_url="https://security.example.com/vuln-1",
            published_at=datetime(2025, 6, 1, tzinfo=timezone.utc),
            event_type=EventType.NEWS,
            organization="SecurityTeam",
            tags=["security"],
            extra_metadata={},
            collector_id="rss",
            content_hash="test_hash_002",
        )
        await event_repo.create(
            title="Event Two: AI Hackathon Registration Open",
            summary="Register for the global AI hackathon happening next month with prizes worth $50,000.",
            source="hackathon-site",
            source_url="https://hackathon.example.com/register",
            published_at=datetime(2025, 6, 2, tzinfo=timezone.utc),
            event_type=EventType.ANNOUNCEMENT,
            organization="HackOrg",
            tags=["hackathon"],
            extra_metadata={},
            collector_id="rss",
            content_hash="test_hash_003",
        )
        await db_session.commit()

        service = PipelineService(db_session)
        summary = await service.process_all_unprocessed()
        await db_session.commit()

        assert summary["total"] == 2
        assert summary["processed"] == 2
        assert summary["failed"] == 0
        assert len(summary["results"]) == 2

    @pytest.mark.asyncio
    async def test_process_single_not_found(self, db_session):
        """Processing a non-existent event raises ValueError."""
        from app.services.pipeline.pipeline_service import PipelineService

        service = PipelineService(db_session)
        with pytest.raises(ValueError, match="not found"):
            await service.process_single(uuid.uuid4())

    @pytest.mark.asyncio
    async def test_reprocessing_replaces_existing(self, db_session):
        """Re-processing an event should replace the old ProcessedEvent."""
        from app.repositories.event_repository import EventRepository
        from app.repositories.processed_event_repository import ProcessedEventRepository
        from app.services.pipeline.pipeline_service import PipelineService

        event_repo = EventRepository(db_session)
        event = await event_repo.create(
            title="Reprocess Test Event Title",
            summary="This event will be processed twice to test reprocessing behavior and data integrity.",
            source="test-source",
            source_url="https://example.com/reprocess-test",
            published_at=datetime(2025, 6, 1, tzinfo=timezone.utc),
            event_type=EventType.NEWS,
            organization="TestOrg",
            tags=["test"],
            extra_metadata={},
            collector_id="rss",
            content_hash="test_hash_reprocess",
        )
        await db_session.commit()

        service = PipelineService(db_session)

        # Process first time
        first = await service.process_single(event.id)
        await db_session.commit()
        first_id = first.id

        # Process second time (re-process)
        second = await service.process_single(event.id)
        await db_session.commit()

        # Should be a new ProcessedEvent (different ID)
        assert second.id != first_id
        assert second.collected_event_id == event.id

        # Old one should be gone
        processed_repo = ProcessedEventRepository(db_session)
        old = await processed_repo.get_by_id(first_id)
        assert old is None
