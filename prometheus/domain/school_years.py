import json
import re


def parse_question_year_values(year_value, segment=""):
    year_value = (year_value or "").strip()
    segment = (segment or "").strip()
    if year_value.startswith("{"):
        try:
            legacy_info = json.loads(year_value)
            if isinstance(legacy_info, dict):
                segment = segment or str(legacy_info.get("level", "")).strip()
                legacy_years = legacy_info.get("years", [])
                if not isinstance(legacy_years, list):
                    legacy_years = [legacy_years]
                normalized_years = []
                for value in legacy_years:
                    value = str(value).strip()
                    match = re.search(r"\d+", value)
                    if match and "médio" in segment.casefold():
                        value = f"{match.group()}ª Série"
                    elif match and "fundamental" in segment.casefold():
                        value = f"{match.group()}º Ano"
                    if value:
                        normalized_years.append(value)
                return normalized_years
        except (TypeError, ValueError):
            pass

    return [value.strip() for value in year_value.split(";") if value.strip()]


def format_question_year_info(year_value, segment):
    segment = (segment or "").strip()
    if (year_value or "").strip().startswith("{"):
        try:
            legacy_info = json.loads(year_value)
            if isinstance(legacy_info, dict):
                segment = segment or str(legacy_info.get("level", "")).strip()
        except (TypeError, ValueError):
            pass
    years = parse_question_year_values(year_value, segment)
    year_label = ", ".join(years)
    if segment and year_label:
        return f"{segment} — {year_label}"
    return segment or year_label
