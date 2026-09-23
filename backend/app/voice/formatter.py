import re
from typing import List, Optional
from app.reasoning.models import ReasoningResult, RecommendedNextStep


class SpokenResponseFormatter:
    """Formats structured ReasoningResults into concise, natural speech scripts."""

    METADATA_DISQUALIFIERS = [
        "model scope",
        "model:",
        "target subsystem",
        "document id",
        "doc id",
        "document type",
        "safety classification",
        "safety level",
        "notice:",
        "notice",
        "fictional",
        "demo data",
        "disclaimer",
        "revision:",
        "version:",
        "date:",
        "author:",
        "status:",
        "sop-",
        "chunk",
        "retrieval",
    ]

    @classmethod
    def clean_step_text(cls, raw_step: str) -> Optional[str]:
        """
        Clean markdown, labels, and prefixes from step text, and reject non-actionable metadata.
        Returns cleaned action string or None if the step is metadata/invalid.
        """
        if not raw_step:
            return None

        # 1. Remove markdown markers: bold, italic, headers, blockquotes
        clean = raw_step.strip()
        clean = re.sub(r"\*\*([^*]+)\*\*", r"\1", clean)
        clean = re.sub(r"\*([^*]+)\*", r"\1", clean)
        clean = re.sub(r"__([^_]+)__", r"\1", clean)
        clean = re.sub(r"_([^_]+)_", r"\1", clean)
        clean = re.sub(r"^>+\s*", "", clean)
        clean = re.sub(r"^#+\s*", "", clean)

        # 2. Remove step numbering prefixes (e.g. "Step 1: ", "1. ", "- ")
        clean = re.sub(r"^step\s*\d+\s*[:.-]\s*", "", clean, flags=re.IGNORECASE)
        clean = re.sub(r"^[-*•]\s*", "", clean)
        clean = re.sub(r"^\d+\.\s*", "", clean)
        clean = clean.strip()

        # 3. Check for metadata disqualifiers
        lower_clean = clean.lower()
        if any(marker in lower_clean for marker in cls.METADATA_DISQUALIFIERS):
            return None

        # 4. Require reasonable length for a meaningful action directive
        if len(clean) < 15:
            return None

        # Ensure proper punctuation
        if not clean.endswith("."):
            clean += "."

        return clean

    @classmethod
    def select_actionable_step(cls, steps: List[RecommendedNextStep]) -> Optional[str]:
        """Iterate through recommended steps and return the first genuine actionable instruction."""
        for step_obj in steps:
            cleaned = cls.clean_step_text(step_obj.step)
            if cleaned:
                return cleaned
        return None

    @staticmethod
    def format(result: ReasoningResult) -> str:
        """
        Generate a concise spoken response adhering to voice priorities:
        1. Critical Safety Warnings (mandatory LOTO / high pressure hazards)
        2. Clarifying Questions (if status == 'needs_information')
        3. Core Diagnostic Assessment (first 1-2 concise sentences)
        4. Immediate Next Action (first prioritized procedural step, strictly excluding metadata)
        5. Non-authoritative notice (if referencing pending field contributions)
        """
        parts: List[str] = []

        # 1. Critical Safety Warnings MUST be spoken first when present
        if result.safety_considerations:
            primary_safety = result.safety_considerations[0].strip()
            # Clean markdown from safety string
            primary_safety = re.sub(r"\*\*([^*]+)\*\*", r"\1", primary_safety)
            # Ensure standard audible alert phrasing if not already present
            lower_safety = primary_safety.lower()
            if not lower_safety.startswith("warning") and not lower_safety.startswith("danger") and not lower_safety.startswith("caution"):
                primary_safety = f"Warning: {primary_safety}"
            if not primary_safety.endswith("."):
                primary_safety += "."
            parts.append(primary_safety)

        # 2. Clarifying Questions if information is needed or status is needs_information
        if result.status == "needs_information" and result.clarifying_questions:
            questions = [q.strip() for q in result.clarifying_questions if q.strip()]
            if len(questions) == 1:
                q_text = questions[0]
                if not q_text.endswith("?"):
                    q_text += "?"
                parts.append(f"To assist you: {q_text}")
            elif len(questions) > 1:
                first_q = questions[0].rstrip("?")
                second_q = questions[1].rstrip("?")
                parts.append(f"To assist you: {first_q}, and {second_q.lower()}?")
            return " ".join(parts).strip()

        # 3. Assessment summary (first 1-2 sentences of assessment)
        if result.assessment:
            clean_assessment = result.assessment.strip()
            clean_assessment = re.sub(r"\*\*([^*]+)\*\*", r"\1", clean_assessment)
            sentences = [s.strip() for s in clean_assessment.split(". ") if s.strip()]
            if sentences:
                spoken_assessment = sentences[0]
                if not spoken_assessment.endswith("."):
                    spoken_assessment += "."
                if len(sentences) > 1 and len(spoken_assessment) < 70:
                    second_sentence = sentences[1]
                    if not second_sentence.endswith("."):
                        second_sentence += "."
                    spoken_assessment = f"{spoken_assessment} {second_sentence}"
                parts.append(spoken_assessment)

        # 4. Immediate Next Step (prioritized physical action, strictly excluding metadata)
        if result.recommended_next_steps:
            action_step = SpokenResponseFormatter.select_actionable_step(result.recommended_next_steps)
            if action_step:
                parts.append(f"Recommended next step: {action_step}")

        # 5. Non-authoritative contribution indicator if relevant
        has_pending_contrib = any(
            cite.metadata.get("provenance_type") == "TECHNICIAN_CONTRIBUTION" or
            cite.metadata.get("verification_status") == "PENDING_REVIEW" or
            cite.document_type == "technician_contribution"
            for cite in result.citations
        )
        if has_pending_contrib:
            parts.append("Note: this guidance references pending field observations.")

        return " ".join(parts).strip()
