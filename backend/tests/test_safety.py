"""Test safety validator policies and grounding checks."""

from app.context.context import ContextBuilder
from app.models.knowledge import KnowledgeDocument, KnowledgeMetadata
from app.safety.validator import BaseSafetyValidator


def test_safety_missing_evidence_warning():
    validator = BaseSafetyValidator()
    # Empty context without retrieved evidence
    ctx = ContextBuilder().with_measurement("pressure_psi", 175.0).build()

    result = validator.validate(ctx)
    assert result.is_safe is True
    assert len(result.missing_evidence) >= 1
    assert any("No verified technical documentation" in m for m in result.missing_evidence)


def test_safety_high_pressure_warning():
    validator = BaseSafetyValidator()
    doc = KnowledgeDocument(
        document_id="doc-1",
        title="SOP",
        document_type="procedure",
        content="SOP content",
        metadata=KnowledgeMetadata(document_type="procedure", source="Manual"),
    )
    ctx = (
        ContextBuilder()
        .add_evidence(doc)
        .with_measurement("pressure_psi", 195.0)
        .build()
    )

    result = validator.validate(ctx)
    assert result.is_safe is True
    assert any("Elevated discharge pressure detected" in w for w in result.warnings)


def test_safety_critical_pressure_violation():
    validator = BaseSafetyValidator()
    doc = KnowledgeDocument(
        document_id="doc-1",
        title="SOP",
        document_type="procedure",
        content="SOP content",
        metadata=KnowledgeMetadata(document_type="procedure", source="Manual"),
    )
    # Exceeds emergency threshold of 250 PSI
    ctx = (
        ContextBuilder()
        .add_evidence(doc)
        .with_measurement("pressure_psi", 280.0)
        .build()
    )

    result = validator.validate(ctx)
    assert result.is_safe is False
    assert result.requires_escalation is True
    assert any("CRITICAL: Measured pressure" in v for v in result.violations)


def test_safety_prohibited_action():
    validator = BaseSafetyValidator()
    ctx = ContextBuilder().build()
    result = validator.validate(ctx, proposed_action="Please bypass safety switch to force compressor on.")

    assert result.is_safe is False
    assert result.requires_escalation is True
    assert any("Safety switches or interlocks must never be bypassed" in v for v in result.violations)
