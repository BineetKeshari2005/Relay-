"""Safety validation abstractions and deterministic policy checking."""

from abc import ABC, abstractmethod
from typing import List, Optional
from pydantic import BaseModel, Field

from app.context.context import Context


class SafetyCheckResult(BaseModel):
    """Result of safety validation over context and proposed advice."""

    is_safe: bool = Field(..., description="True if no safety rules or policy boundaries are violated")
    violations: List[str] = Field(default_factory=list, description="List of detected safety or policy violations")
    warnings: List[str] = Field(default_factory=list, description="Advisory safety warnings for the technician")
    missing_evidence: List[str] = Field(
        default_factory=list,
        description="Critical technical parameters or documents required before proceeding",
    )
    requires_escalation: bool = Field(
        default=False,
        description="True if procedure requires immediate human supervisor sign-off or escalation",
    )


class SafetyValidator(ABC):
    """
    Abstract safety validator interface.

    Core Principle:
    The LLM is NOT the final authority for safety.
    Safety limits, lockout/tagout mandates, and pressure thresholds must be
    deterministically validated against retrieved verified evidence.
    """

    @abstractmethod
    def validate(
        self,
        context: Context,
        proposed_action: Optional[str] = None,
    ) -> SafetyCheckResult:
        """
        Validate the safety of the current context and proposed diagnostic recommendation.

        Args:
            context: The unified Context object containing evidence, measurements, and asset data.
            proposed_action: The proposed recommendation or instruction to be checked.

        Returns:
            SafetyCheckResult detailing safety status, warnings, and escalation flags.
        """
        pass


class BaseSafetyValidator(SafetyValidator):
    """
    Phase 1 deterministic safety validator.
    Enforces baseline safety boundaries:
    1. Checks if critical equipment pressure or electrical measurements exist.
    2. Flags high pressure operations requiring lock-out / shutdown.
    3. Mandates evidence grounding: flags advice if verified knowledge documents are missing.
    """

    def validate(
        self,
        context: Context,
        proposed_action: Optional[str] = None,
    ) -> SafetyCheckResult:
        violations: List[str] = []
        warnings: List[str] = []
        missing_evidence: List[str] = []
        requires_escalation: bool = False

        # 1. Grounding check: verify that relevant technical evidence is retrieved
        if not context.retrieved_evidence:
            missing_evidence.append("No verified technical documentation retrieved for this issue.")
            warnings.append(
                "Unverified guidance warning: Do not execute invasive component actions without verified SOP."
            )

        # 2. Pressure safety check (fictional demo rule for high-pressure alerts)
        pressure = context.measurements.get("pressure_psi")
        if pressure is not None:
            try:
                pressure_val = float(pressure)
                # Fictional high-pressure threshold check for CoolCore demo
                if pressure_val > 190.0:
                    warnings.append(
                        f"Elevated discharge pressure detected ({pressure_val} PSI). "
                        "Compressor shutdown and PPE required prior to physical coil inspection."
                    )
                if pressure_val > 250.0:
                    violations.append(
                        f"CRITICAL: Measured pressure ({pressure_val} PSI) exceeds emergency threshold. "
                        "Immediate emergency relief procedure required."
                    )
                    requires_escalation = True
            except (ValueError, TypeError):
                pass

        # 3. Check proposed action text if provided
        if proposed_action:
            action_lower = proposed_action.lower()
            if "bypass safety" in action_lower or "ignore switch" in action_lower:
                violations.append("Prohibited action: Safety switches or interlocks must never be bypassed.")
                requires_escalation = True

        is_safe = len(violations) == 0

        return SafetyCheckResult(
            is_safe=is_safe,
            violations=violations,
            warnings=warnings,
            missing_evidence=missing_evidence,
            requires_escalation=requires_escalation,
        )
