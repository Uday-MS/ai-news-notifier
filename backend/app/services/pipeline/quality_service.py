"""Stage 7 — Quality Validation Service.

Validates that all required pipeline outputs exist and determines
the final processing status: READY, PARTIAL, or FAILED.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from app.models.processed_event import AICategory, ProcessingStatus


@dataclass
class QualityResult:
    """Output of quality validation."""

    status: ProcessingStatus
    issues: list[str] = field(default_factory=list)


class QualityService:
    """Validates completeness of pipeline processing output."""

    def validate(
        self,
        cleaned_title: str,
        cleaned_summary: str,
        ai_category: AICategory | None,
        ai_tags: list[str] | None,
        entities: dict | None,
        importance_score: int | None,
        importance_reason: str,
        ai_summary: str,
        stage_failures: list[str] | None = None,
    ) -> QualityResult:
        """Validate all pipeline outputs and determine processing status.

        Args:
            stage_failures: List of stage names that failed during processing.

        Returns:
            QualityResult with status and any issues found.
        """
        issues: list[str] = []
        failures = stage_failures or []

        # ── Critical checks (cause FAILED) ───────────────────────────────

        # Cleaning must succeed
        if not cleaned_title or not cleaned_title.strip():
            issues.append("Missing cleaned title.")
        if not cleaned_summary or not cleaned_summary.strip():
            issues.append("Missing cleaned summary.")

        # If cleaning stage itself failed, that's critical
        if "cleaning" in failures:
            issues.append("Cleaning stage failed.")

        # ── Important checks (cause PARTIAL) ─────────────────────────────

        if ai_category is None:
            issues.append("Missing classification.")

        if importance_score is None:
            issues.append("Missing importance score.")

        if not ai_summary or not ai_summary.strip():
            issues.append("Missing AI summary.")

        # ── Optional checks (noted but don't affect status) ──────────────

        if not ai_tags:
            issues.append("No tags extracted.")

        if not entities or all(len(v) == 0 for v in entities.values()):
            issues.append("No entities extracted.")

        if not importance_reason or not importance_reason.strip():
            issues.append("Missing importance reason.")

        # ── Determine status ─────────────────────────────────────────────

        critical_issues = [
            i for i in issues
            if "cleaned title" in i.lower()
            or "cleaned summary" in i.lower()
            or "cleaning stage" in i.lower()
        ]

        important_issues = [
            i for i in issues
            if "classification" in i.lower()
            or "importance score" in i.lower()
            or "ai summary" in i.lower()
        ]

        if critical_issues:
            status = ProcessingStatus.FAILED
        elif important_issues:
            status = ProcessingStatus.PARTIAL
        else:
            status = ProcessingStatus.READY

        return QualityResult(status=status, issues=issues)
