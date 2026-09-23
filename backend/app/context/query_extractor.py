"""Deterministic extraction of facts from technician queries without an LLM."""

import re
from typing import Any, Dict, List, Optional

from app.context.assembled_context import ExtractedQueryFacts


class QueryContextExtractor:
    """
    Deterministic rule-based extractor for technician queries.
    Never invents unstated facts, models, or measurements.
    """

    # Error code pattern: E followed by 1 to 3 digits (e.g. E17, E01, E22)
    ERROR_CODE_REGEX = re.compile(r"\b([E|e]\d{1,3})\b")

    # Equipment model pattern (e.g. ACX-420, ACX420)
    MODEL_REGEX = re.compile(r"\b(ACX-?\d{3,4})\b", re.IGNORECASE)

    # Unit reference pattern (e.g. "unit 017", "unit #017", "unit-017", "pad 17")
    UNIT_REF_REGEX = re.compile(
        r"\b(?:unit|pad)\s*(?:#|no\.?)?\s*([a-zA-Z0-9_-]+)\b",
        re.IGNORECASE,
    )

    # Full asset ID pattern (e.g. ACX-420-017)
    ASSET_ID_REGEX = re.compile(r"\b(ACX-\d{3}-\d{3})\b", re.IGNORECASE)

    # Pressure measurement pattern: number followed by PSI / psi / pounds
    PRESSURE_REGEX = re.compile(
        r"(\d+(?:\.\d+)?)\s*(?:psi|PSI|pounds\s+per\s+square\s+inch)\b"
    )

    # Temperature measurement pattern: number followed by F / °F / C / °C / deg
    TEMP_REGEX = re.compile(
        r"(\d+(?:\.\d+)?)\s*(?:°\s*[FfCc]|deg(?:rees)?\s*[FfCc]|[FfCc]\b)"
    )

    # Voltage measurement pattern: number followed by V / VAC / VDC / volts
    VOLTAGE_REGEX = re.compile(
        r"(\d+(?:\.\d+)?)\s*(?:v(?:ac|dc)?|volts?)\b",
        re.IGNORECASE,
    )

    # Recurrence keywords
    REPEAT_KEYWORDS = ["again", "repeat", "recurring", "recurrent", "still happening", "tripped again"]

    def extract(self, query: str) -> ExtractedQueryFacts:
        """Parse explicit facts from the technician's query."""
        clean_query = query.strip()
        measurements: Dict[str, Any] = {}
        observations: List[str] = []

        # 1. Extract Error Code
        error_code: Optional[str] = None
        error_match = self.ERROR_CODE_REGEX.search(clean_query)
        if error_match:
            error_code = error_match.group(1).upper()

        # 2. Extract Equipment Model
        asset_model: Optional[str] = None
        model_match = self.MODEL_REGEX.search(clean_query)
        if model_match:
            raw_model = model_match.group(1).upper()
            asset_model = raw_model if "-" in raw_model else f"{raw_model[:3]}-{raw_model[3:]}"

        # 3. Extract Asset Reference or Exact Asset ID
        asset_reference: Optional[str] = None
        exact_id_match = self.ASSET_ID_REGEX.search(clean_query)
        if exact_id_match:
            asset_reference = exact_id_match.group(1).upper()
        else:
            unit_match = self.UNIT_REF_REGEX.search(clean_query)
            if unit_match:
                asset_reference = f"unit {unit_match.group(1)}"

        # 4. Extract Measurements
        pressure_match = self.PRESSURE_REGEX.search(clean_query)
        if pressure_match:
            measurements["pressure_psi"] = float(pressure_match.group(1))

        temp_match = self.TEMP_REGEX.search(clean_query)
        if temp_match:
            measurements["temperature"] = float(temp_match.group(1))

        voltage_match = self.VOLTAGE_REGEX.search(clean_query)
        if voltage_match:
            measurements["voltage"] = float(voltage_match.group(1))

        # 5. Extract Recurrence Flag
        query_lower = clean_query.lower()
        is_repeat = any(k in query_lower for k in self.REPEAT_KEYWORDS)

        # 6. Extract Obvious Symptom Observations
        if "pressure is around" in query_lower or "high pressure" in query_lower:
            observations.append("elevated_pressure_reported")
        if "tripped" in query_lower or "trip" in query_lower:
            observations.append("system_trip_lockout")
        if "replaced" in query_lower and "sensor" in query_lower:
            observations.append("past_sensor_replacement_referenced")

        return ExtractedQueryFacts(
            raw_query=clean_query,
            asset_reference=asset_reference,
            asset_model=asset_model,
            error_code=error_code,
            measurements=measurements,
            is_repeat_issue=is_repeat,
            observations=observations,
        )
