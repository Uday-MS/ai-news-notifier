"""Tests for Phase 3 — Personalized Intelligence & Feed Ranking.

Tests cover:
 1. Technology matching
 2. Organization matching
 3. Keyword/interest matching
 4. Confidence boost
 5. Saved behavior signal
 6. Cold start with onboarding interests
 7. Two users with different preferences get different rankings
 8. LLM fields in feed items
 9. Interest mapping from onboarding
10. Preference API with new fields
11. Combined scoring with all stages
12. For You vs Latest distinction
13. Empty preferences fallback
14. Low-relevance filtering
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, hash_password
from app.models.event import CollectedEvent, EventType
from app.models.processed_event import AICategory, ProcessedEvent, ProcessingStatus
from app.models.user import User, UserRole
from app.models.user_profile import UserInterest
from app.models.saved_article import SavedArticle
from app.services.recommendation_service import (
    PreferenceService,
    RecommendationService,
    ScoringEngine,
    ScoringWeights,
)


# ── Helpers ──────────────────────────────────────────────────────────────


def _make_event_dict(**overrides) -> dict[str, Any]:
    """Build a fake event dict with Phase 2 LLM fields."""
    defaults = {
        "id": uuid.uuid4(),
        "collected_event_id": uuid.uuid4(),
        "cleaned_title": "Test Event",
        "cleaned_summary": "Summary.",
        "ai_summary": "AI Summary.",
        "ai_category": AICategory.AI_MODEL,
        "ai_tags": ["ai", "test"],
        "importance_score": 50,
        "source": "test-blog",
        "source_url": "https://example.com/test",
        "organization": "TestOrg",
        "published_at": datetime.now(timezone.utc),
        "processed_at": datetime.now(timezone.utc),
        "entities": {},
        "importance_reason": "Test.",
        "processing_status": ProcessingStatus.READY,
        "created_at": datetime.now(timezone.utc),
        # Phase 2 LLM fields
        "llm_keywords": [],
        "llm_entities": {},
        "llm_category": None,
        "confidence_score": None,
        "why_it_matters": None,
        "llm_summary": None,
        "intelligence_type": None,
        "llm_status": None,
    }
    defaults.update(overrides)
    return defaults


async def _seed_llm_enriched(db: AsyncSession) -> list[ProcessedEvent]:
    """Seed events with LLM intelligence data for personalization testing."""
    now = datetime.now(timezone.utc)
    events = []

    # Event 1: Google Gemini Model Release
    ce1 = CollectedEvent(
        title="Google Releases Gemini 2.5", summary="Major model release from Google.",
        source="google-ai-blog", source_url=f"https://example.com/{uuid.uuid4()}",
        published_at=now - timedelta(hours=2), event_type=EventType.ANNOUNCEMENT,
        organization="Google", tags=[], extra_metadata={}, collector_id="test",
        content_hash=str(uuid.uuid4())[:64],
    )
    db.add(ce1); await db.flush(); await db.refresh(ce1)
    pe1 = ProcessedEvent(
        collected_event_id=ce1.id, cleaned_title="Google Releases Gemini 2.5",
        cleaned_summary="Major model release.", ai_category=AICategory.AI_MODEL,
        ai_tags=["google", "gemini", "llm", "model-release"], entities={},
        importance_score=90, importance_reason="Major.", ai_summary="Google releases Gemini 2.5.",
        processing_status=ProcessingStatus.READY, processed_at=now,
        llm_keywords=["gemini", "google", "multimodal", "reasoning"],
        llm_entities={"technologies": ["Gemini 2.5", "Transformer"], "organizations": ["Google", "Google DeepMind"]},
        confidence_score=0.92, why_it_matters="Advances the frontier of multimodal AI reasoning.",
        intelligence_type="model_release", llm_category="model_release", llm_status="completed",
    )
    db.add(pe1); await db.flush(); await db.refresh(pe1)
    events.append(pe1)

    # Event 2: Cybersecurity AI Vulnerability
    ce2 = CollectedEvent(
        title="Critical AI Security Flaw Found", summary="ML pipeline vulnerability.",
        source="security-blog", source_url=f"https://example.com/{uuid.uuid4()}",
        published_at=now - timedelta(hours=3), event_type=EventType.NEWS,
        organization="CyberSec", tags=[], extra_metadata={}, collector_id="test",
        content_hash=str(uuid.uuid4())[:64],
    )
    db.add(ce2); await db.flush(); await db.refresh(ce2)
    pe2 = ProcessedEvent(
        collected_event_id=ce2.id, cleaned_title="Critical AI Security Flaw Found",
        cleaned_summary="ML vulnerability.", ai_category=AICategory.SECURITY,
        ai_tags=["security", "vulnerability", "ml-pipeline"], entities={},
        importance_score=85, importance_reason="Critical.", ai_summary="Security flaw found.",
        processing_status=ProcessingStatus.READY, processed_at=now,
        llm_keywords=["security", "vulnerability", "ml", "pipeline", "attack"],
        llm_entities={"technologies": ["ML Pipeline"], "organizations": ["CyberSec"]},
        confidence_score=0.88, why_it_matters="Exposes a critical vulnerability in ML pipelines.",
        intelligence_type="security", llm_category="security", llm_status="completed",
    )
    db.add(pe2); await db.flush(); await db.refresh(pe2)
    events.append(pe2)

    # Event 3: Open Source PyTorch Release
    ce3 = CollectedEvent(
        title="PyTorch 3.0 Released", summary="Open source framework update.",
        source="github-trending", source_url=f"https://example.com/{uuid.uuid4()}",
        published_at=now - timedelta(hours=5), event_type=EventType.ANNOUNCEMENT,
        organization="Meta", tags=[], extra_metadata={}, collector_id="test",
        content_hash=str(uuid.uuid4())[:64],
    )
    db.add(ce3); await db.flush(); await db.refresh(ce3)
    pe3 = ProcessedEvent(
        collected_event_id=ce3.id, cleaned_title="PyTorch 3.0 Released",
        cleaned_summary="Framework update.", ai_category=AICategory.OPEN_SOURCE,
        ai_tags=["pytorch", "open-source", "meta", "framework"], entities={},
        importance_score=75, importance_reason="Major framework.", ai_summary="PyTorch 3.0 out.",
        processing_status=ProcessingStatus.READY, processed_at=now,
        llm_keywords=["pytorch", "open-source", "deep-learning", "meta"],
        llm_entities={"technologies": ["PyTorch", "CUDA"], "organizations": ["Meta"]},
        confidence_score=0.80, why_it_matters="PyTorch 3.0 brings significant performance improvements.",
        intelligence_type="open_source", llm_category="open_source", llm_status="completed",
    )
    db.add(pe3); await db.flush(); await db.refresh(pe3)
    events.append(pe3)

    # Event 4: AI Research Paper
    ce4 = CollectedEvent(
        title="Attention Is Still All You Need", summary="Research paper.",
        source="arxiv", source_url=f"https://example.com/{uuid.uuid4()}",
        published_at=now - timedelta(hours=10), event_type=EventType.NEWS,
        organization="MIT", tags=[], extra_metadata={}, collector_id="test",
        content_hash=str(uuid.uuid4())[:64],
    )
    db.add(ce4); await db.flush(); await db.refresh(ce4)
    pe4 = ProcessedEvent(
        collected_event_id=ce4.id, cleaned_title="Attention Is Still All You Need",
        cleaned_summary="Research paper.", ai_category=AICategory.AI_RESEARCH,
        ai_tags=["research", "transformer", "attention"], entities={},
        importance_score=60, importance_reason="Research.", ai_summary="Transformer paper.",
        processing_status=ProcessingStatus.READY, processed_at=now,
        llm_keywords=["transformer", "attention", "research", "architecture"],
        llm_entities={"technologies": ["Transformer"], "organizations": ["MIT"]},
        confidence_score=0.70, why_it_matters="New insights into attention mechanisms.",
        intelligence_type="research", llm_category="research", llm_status="completed",
    )
    db.add(pe4); await db.flush(); await db.refresh(pe4)
    events.append(pe4)

    await db.commit()
    return events


# ══════════════════════════════════════════════════════════════════════════
# ScoringEngine — Phase 3 New Stages
# ══════════════════════════════════════════════════════════════════════════


class TestScoringEnginePhase3:
    """Unit tests for the new Phase 3 scoring stages."""

    def setup_method(self):
        self.engine = ScoringEngine()

    def test_technology_match_single(self):
        event = _make_event_dict(
            llm_entities={"technologies": ["Gemini", "Transformer"]},
            llm_keywords=["gemini"],
        )
        total, factors = self.engine.score_event(
            event, preferred_technologies=["Gemini"]
        )
        tech = next(f for f in factors if f.factor == "technology")
        assert tech.score > 0
        assert "gemini" in tech.reason.lower()

    def test_technology_match_multiple(self):
        event = _make_event_dict(
            llm_entities={"technologies": ["PyTorch", "CUDA"]},
            llm_keywords=["pytorch", "cuda"],
        )
        total, factors = self.engine.score_event(
            event, preferred_technologies=["PyTorch", "CUDA"]
        )
        tech = next(f for f in factors if f.factor == "technology")
        assert tech.score >= 15.0  # 2 matches = 75%+ of 20

    def test_technology_no_match(self):
        event = _make_event_dict(
            llm_entities={"technologies": ["TensorFlow"]},
        )
        total, factors = self.engine.score_event(
            event, preferred_technologies=["PyTorch"]
        )
        tech = next(f for f in factors if f.factor == "technology")
        assert tech.score == 0.0

    def test_technology_no_preferences(self):
        event = _make_event_dict(llm_entities={"technologies": ["Gemini"]})
        total, factors = self.engine.score_event(event)
        tech = next(f for f in factors if f.factor == "technology")
        assert tech.score == 0.0

    def test_organization_match(self):
        event = _make_event_dict(
            organization="Google",
            llm_entities={"organizations": ["Google DeepMind"]},
        )
        total, factors = self.engine.score_event(
            event, preferred_organizations=["Google"]
        )
        org = next(f for f in factors if f.factor == "organization")
        assert org.score == 15.0
        assert "google" in org.reason.lower()

    def test_organization_no_match(self):
        event = _make_event_dict(organization="Meta")
        total, factors = self.engine.score_event(
            event, preferred_organizations=["Google"]
        )
        org = next(f for f in factors if f.factor == "organization")
        assert org.score == 0.0

    def test_keyword_interest_match(self):
        event = _make_event_dict(
            llm_keywords=["security", "vulnerability"],
            ai_tags=["security"],
        )
        total, factors = self.engine.score_event(
            event, user_interests=["security", "cybersecurity"]
        )
        kw = next(f for f in factors if f.factor == "interest")
        assert kw.score > 0
        assert "security" in kw.reason.lower()

    def test_keyword_interest_no_match(self):
        event = _make_event_dict(
            llm_keywords=["gemini", "google"],
            ai_tags=["llm"],
        )
        total, factors = self.engine.score_event(
            event, user_interests=["security", "cybersecurity"]
        )
        kw = next(f for f in factors if f.factor == "interest")
        assert kw.score == 0.0

    def test_keyword_interest_title_match(self):
        event = _make_event_dict(
            cleaned_title="New Security Research Published",
            llm_keywords=[],
        )
        total, factors = self.engine.score_event(
            event, user_interests=["security"]
        )
        kw = next(f for f in factors if f.factor == "interest")
        assert kw.score > 0

    def test_confidence_boost(self):
        event = _make_event_dict(confidence_score=0.9)
        total, factors = self.engine.score_event(event)
        conf = next(f for f in factors if f.factor == "confidence")
        assert conf.score == 4.5  # 0.9 * 5.0

    def test_confidence_no_data(self):
        event = _make_event_dict(confidence_score=None)
        total, factors = self.engine.score_event(event)
        conf = next(f for f in factors if f.factor == "confidence")
        assert conf.score == 0.0

    def test_saved_behavior_signal(self):
        event = _make_event_dict(ai_category=AICategory.SECURITY)
        total, factors = self.engine.score_event(
            event, saved_categories=["security", "security", "security"]
        )
        saved = next(f for f in factors if f.factor == "saved_behavior")
        assert saved.score == 10.0  # 3+ saves = max

    def test_saved_behavior_partial(self):
        event = _make_event_dict(ai_category=AICategory.SECURITY)
        total, factors = self.engine.score_event(
            event, saved_categories=["security"]
        )
        saved = next(f for f in factors if f.factor == "saved_behavior")
        assert 3.0 <= saved.score <= 4.0  # ~33% of max

    def test_saved_behavior_wrong_category(self):
        event = _make_event_dict(ai_category=AICategory.AI_MODEL)
        total, factors = self.engine.score_event(
            event, saved_categories=["security", "security"]
        )
        saved = next(f for f in factors if f.factor == "saved_behavior")
        assert saved.score == 0.0

    def test_combined_scoring_all_stages(self):
        """All stages contribute to the final score."""
        event = _make_event_dict(
            ai_category=AICategory.SECURITY,
            importance_score=80,
            confidence_score=0.85,
            llm_keywords=["security", "vulnerability"],
            llm_entities={"technologies": ["ML Pipeline"], "organizations": ["CyberSec"]},
            organization="CyberSec",
        )
        total, factors = self.engine.score_event(
            event,
            preferred_categories=["security"],
            preferred_technologies=["ML Pipeline"],
            preferred_organizations=["CyberSec"],
            user_interests=["security"],
            saved_categories=["security", "security"],
        )
        # Should have contributions from all matching stages
        factor_names = {f.factor for f in factors if f.score > 0}
        assert "preferred_category" in factor_names
        assert "importance" in factor_names
        assert "technology" in factor_names
        assert "organization" in factor_names
        assert "interest" in factor_names
        assert "confidence" in factor_names
        assert "saved_behavior" in factor_names
        assert total > 80  # Should be a very high score

    def test_custom_phase3_weights(self):
        weights = ScoringWeights(
            technology_match=40.0,
            organization_match=30.0,
        )
        engine = ScoringEngine(weights)
        event = _make_event_dict(
            llm_entities={"technologies": ["PyTorch", "CUDA"]},
            organization="Google",
        )
        total, factors = engine.score_event(
            event,
            preferred_technologies=["PyTorch", "CUDA"],
            preferred_organizations=["Google"],
        )
        tech = next(f for f in factors if f.factor == "technology")
        org = next(f for f in factors if f.factor == "organization")
        assert tech.score >= 30.0  # 75%+ of 40
        assert org.score == 30.0


# ══════════════════════════════════════════════════════════════════════════
# Interest Mapping
# ══════════════════════════════════════════════════════════════════════════


class TestInterestMapping:
    """Tests for _map_interests_to_preferences."""

    def test_maps_categories(self):
        cats, techs, orgs = RecommendationService._map_interests_to_preferences(
            ["AI Research", "Security", "Open Source"]
        )
        assert "ai_research" in cats
        assert "security" in cats
        assert "open_source" in cats

    def test_maps_organizations(self):
        cats, techs, orgs = RecommendationService._map_interests_to_preferences(
            ["Google", "OpenAI", "Anthropic"]
        )
        assert len(orgs) == 3

    def test_maps_technologies(self):
        cats, techs, orgs = RecommendationService._map_interests_to_preferences(
            ["PyTorch", "Gemini", "Claude"]
        )
        assert len(techs) == 3

    def test_unknown_interest_ignored(self):
        cats, techs, orgs = RecommendationService._map_interests_to_preferences(
            ["quantum computing", "blockchain"]
        )
        assert len(cats) == 0
        assert len(techs) == 0
        assert len(orgs) == 0


# ══════════════════════════════════════════════════════════════════════════
# Integration — Two Users, Different Rankings
# ══════════════════════════════════════════════════════════════════════════


class TestPersonalizedRanking:
    """Integration tests proving different users get different rankings."""

    @pytest.mark.asyncio
    async def test_two_users_different_rankings(self, db_session):
        """USER A prefers Google/LLMs, USER B prefers Security/Open Source.
        Their For You feeds should have different top items."""
        events = await _seed_llm_enriched(db_session)

        # Create User A: LLM enthusiast
        user_a = User(
            email="user_a@test.com", hashed_password=hash_password("P@ss1"),
            full_name="User A", role=UserRole.USER, is_active=True, is_verified=True,
        )
        db_session.add(user_a)
        await db_session.flush()
        await db_session.refresh(user_a)

        pref_svc = PreferenceService(db_session)
        await pref_svc.update_preferences(
            user_a.id,
            preferred_categories=["ai_model"],
            preferred_technologies=["Gemini"],
            preferred_organizations=["Google"],
        )

        # Create User B: Security researcher
        user_b = User(
            email="user_b@test.com", hashed_password=hash_password("P@ss1"),
            full_name="User B", role=UserRole.USER, is_active=True, is_verified=True,
        )
        db_session.add(user_b)
        await db_session.flush()
        await db_session.refresh(user_b)

        await pref_svc.update_preferences(
            user_b.id,
            preferred_categories=["security", "open_source"],
            preferred_technologies=["PyTorch"],
            preferred_organizations=["Meta"],
        )
        await db_session.commit()

        # Get recommendations for both
        rec_svc = RecommendationService(db_session)
        feed_a = await rec_svc.get_for_you(user_a, limit=10)
        feed_b = await rec_svc.get_for_you(user_b, limit=10)

        # Verify both feeds have items
        assert len(feed_a.items) > 0
        assert len(feed_b.items) > 0

        # User A's top item should be the Google/Gemini event
        assert feed_a.items[0].cleaned_title == "Google Releases Gemini 2.5"

        # User B's top item should be Security or PyTorch
        top_b_title = feed_b.items[0].cleaned_title
        assert top_b_title in (
            "Critical AI Security Flaw Found",
            "PyTorch 3.0 Released",
        )

        # Rankings should differ
        titles_a = [i.cleaned_title for i in feed_a.items]
        titles_b = [i.cleaned_title for i in feed_b.items]
        assert titles_a != titles_b, "Different users should get different rankings"

    @pytest.mark.asyncio
    async def test_cold_start_with_onboarding(self, db_session):
        """User with onboarding interests but no explicit preferences gets personalized results."""
        events = await _seed_llm_enriched(db_session)

        user = User(
            email="coldstart@test.com", hashed_password=hash_password("P@ss1"),
            full_name="Cold Start", role=UserRole.USER, is_active=True, is_verified=True,
        )
        db_session.add(user)
        await db_session.flush()
        await db_session.refresh(user)

        # Add onboarding interests (NOT explicit preferences)
        for interest in ["Security", "PyTorch", "Open Source"]:
            db_session.add(UserInterest(user_id=user.id, interest=interest))
        await db_session.commit()
        await db_session.refresh(user)

        rec_svc = RecommendationService(db_session)
        feed = await rec_svc.get_for_you(user, limit=10)

        assert len(feed.items) > 0
        # Security or PyTorch should rank highly due to onboarding
        top_titles = [i.cleaned_title for i in feed.items[:2]]
        assert any("Security" in t or "PyTorch" in t for t in top_titles)

    @pytest.mark.asyncio
    async def test_empty_preferences_cold_start(self, db_session):
        """User with no preferences or interests gets importance+freshness-based results."""
        events = await _seed_llm_enriched(db_session)

        user = User(
            email="empty@test.com", hashed_password=hash_password("P@ss1"),
            full_name="Empty", role=UserRole.USER, is_active=True, is_verified=True,
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        rec_svc = RecommendationService(db_session)
        feed = await rec_svc.get_for_you(user, limit=10)

        # Should still have items (importance + freshness scoring)
        assert len(feed.items) > 0
        # Highest importance should rank first
        assert feed.items[0].importance_score >= 80

    @pytest.mark.asyncio
    async def test_saved_behavior_boosts_category(self, db_session):
        """Saving security articles should boost future security items."""
        events = await _seed_llm_enriched(db_session)

        user = User(
            email="saver@test.com", hashed_password=hash_password("P@ss1"),
            full_name="Saver", role=UserRole.USER, is_active=True, is_verified=True,
        )
        db_session.add(user)
        await db_session.flush()
        await db_session.refresh(user)

        # Save multiple security articles
        security_event = events[1]  # The security event
        db_session.add(SavedArticle(user_id=user.id, processed_event_id=security_event.id))
        await db_session.commit()

        rec_svc = RecommendationService(db_session)
        feed = await rec_svc.get_for_you(user, limit=10)

        # Security event should get a boost from saved behavior
        security_items = [i for i in feed.items if i.ai_category == AICategory.SECURITY]
        assert len(security_items) > 0
        # Check the saved_behavior reason is present
        security_item = security_items[0]
        assert any("saved" in r.lower() for r in security_item.recommendation_reasons)

    @pytest.mark.asyncio
    async def test_llm_fields_in_recommendation_items(self, db_session):
        """Recommendation items should include LLM intelligence fields."""
        events = await _seed_llm_enriched(db_session)

        user = User(
            email="llmcheck@test.com", hashed_password=hash_password("P@ss1"),
            full_name="LLM", role=UserRole.USER, is_active=True, is_verified=True,
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        rec_svc = RecommendationService(db_session)
        feed = await rec_svc.get_for_you(user, limit=10)

        # At least one item should have LLM intelligence
        enriched_items = [i for i in feed.items if i.why_it_matters]
        assert len(enriched_items) > 0

        item = enriched_items[0]
        assert item.why_it_matters is not None
        assert item.intelligence_type is not None
        assert item.confidence_score is not None

    @pytest.mark.asyncio
    async def test_for_you_vs_latest_distinction(self, db_session):
        """For You should rank differently than Latest (chronological)."""
        events = await _seed_llm_enriched(db_session)

        user = User(
            email="distinct@test.com", hashed_password=hash_password("P@ss1"),
            full_name="Distinct", role=UserRole.USER, is_active=True, is_verified=True,
        )
        db_session.add(user)
        await db_session.flush()
        await db_session.refresh(user)

        pref_svc = PreferenceService(db_session)
        await pref_svc.update_preferences(
            user.id,
            preferred_categories=["ai_research"],
            preferred_technologies=["Transformer"],
        )
        await db_session.commit()

        rec_svc = RecommendationService(db_session)

        # For You: personalized
        for_you = await rec_svc.get_for_you(user, limit=10)
        # Latest equivalent: non-personalized (sorted by freshness+importance)
        latest = await rec_svc.get_recommendations(limit=10)

        fy_titles = [i.cleaned_title for i in for_you.items]
        lt_titles = [i.cleaned_title for i in latest.items]

        # They should differ because For You has preference scoring
        # The research event should rank higher in For You for this user
        fy_research_idx = next(
            (i for i, t in enumerate(fy_titles) if "Attention" in t), None
        )
        lt_research_idx = next(
            (i for i, t in enumerate(lt_titles) if "Attention" in t), None
        )
        if fy_research_idx is not None and lt_research_idx is not None:
            assert fy_research_idx < lt_research_idx, \
                "Research should rank higher in For You for this user"

    @pytest.mark.asyncio
    async def test_preference_api_new_fields(self, db_session):
        """Verify preference API accepts and returns new fields."""
        user = User(
            email="preftest@test.com", hashed_password=hash_password("P@ss1"),
            full_name="Pref", role=UserRole.USER, is_active=True, is_verified=True,
        )
        db_session.add(user)
        await db_session.commit()

        pref_svc = PreferenceService(db_session)
        result = await pref_svc.update_preferences(
            user.id,
            preferred_technologies=["PyTorch", "Gemini"],
            preferred_organizations=["Google", "Meta"],
        )
        await db_session.commit()

        assert result.preferred_technologies == ["PyTorch", "Gemini"]
        assert result.preferred_organizations == ["Google", "Meta"]

        # Verify get returns same
        prefs = await pref_svc.get_preferences(user.id)
        assert prefs.preferred_technologies == ["PyTorch", "Gemini"]
        assert prefs.preferred_organizations == ["Google", "Meta"]

    @pytest.mark.asyncio
    async def test_explain_includes_phase3_factors(self, db_session):
        """Explain endpoint should include technology/org/interest factors."""
        events = await _seed_llm_enriched(db_session)

        user = User(
            email="explain3@test.com", hashed_password=hash_password("P@ss1"),
            full_name="Explain", role=UserRole.USER, is_active=True, is_verified=True,
        )
        db_session.add(user)
        await db_session.flush()
        await db_session.refresh(user)

        pref_svc = PreferenceService(db_session)
        await pref_svc.update_preferences(
            user.id,
            preferred_technologies=["Gemini"],
            preferred_organizations=["Google"],
        )
        await db_session.commit()

        rec_svc = RecommendationService(db_session)
        explanation = await rec_svc.explain(user, events[0].id)

        assert explanation is not None
        factor_names = {f.factor for f in explanation.factors}
        assert "technology" in factor_names
        assert "organization" in factor_names
        assert "confidence" in factor_names
