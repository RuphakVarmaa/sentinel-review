from app.models.finding import Finding, FindingCreate, LLMFinding, Severity, Category
from typing import List, Optional, Union
import json

# Severity ordering from most to least severe
SEVERITY_ORDER = [
    Severity.critical,
    Severity.high,
    Severity.medium,
    Severity.low,
    Severity.info,
]

SEVERITY_RANK = {s: i for i, s in enumerate(SEVERITY_ORDER)}


def parse_llm_response(
    raw: Union[str, dict],
    category: Category
) -> List[FindingCreate]:
    """Parse LLM JSON response into list of FindingCreate.

    Handles both str (JSON) and dict inputs.
    If raw is a dict with 'findings' key, uses that list.
    Maps severity strings to Severity enum (case-insensitive).
    Maps category strings to Category enum, fallback to provided category.
    Skips findings with missing required fields (title, explanation).
    Returns empty list on any parse error.
    """
    try:
        if isinstance(raw, str):
            data = json.loads(raw)
        else:
            data = raw

        if isinstance(data, dict) and 'findings' in data:
            findings_raw = data['findings']
        elif isinstance(data, list):
            findings_raw = data
        else:
            return []

        results = []
        for item in findings_raw:
            if not isinstance(item, dict):
                continue

            title = item.get('title')
            explanation = item.get('explanation')

            # Skip findings missing required fields
            if not title or not explanation:
                continue

            # Parse severity
            severity_str = str(item.get('severity', 'info')).lower().strip()
            try:
                severity = Severity(severity_str)
            except ValueError:
                severity = Severity.info

            # Parse category
            category_str = str(item.get('category', '')).lower().strip()
            try:
                parsed_category = Category(category_str)
            except ValueError:
                parsed_category = category

            # Parse optional integer fields
            line_start = item.get('line_start')
            line_end = item.get('line_end')
            if line_start is not None:
                try:
                    line_start = int(line_start)
                except (TypeError, ValueError):
                    line_start = None
            if line_end is not None:
                try:
                    line_end = int(line_end)
                except (TypeError, ValueError):
                    line_end = None

            finding = FindingCreate(
                category=parsed_category,
                severity=severity,
                file_path=item.get('file_path') or None,
                line_start=line_start,
                line_end=line_end,
                title=str(title).strip(),
                explanation=str(explanation).strip(),
                suggested_fix=item.get('suggested_fix') or None,
                why_it_matters=item.get('why_it_matters') or None,
                cwe_id=item.get('cwe_id') or None,
            )
            results.append(finding)

        return results

    except Exception:
        return []


def compute_overall_severity(
    findings: List[Union[Finding, FindingCreate]]
) -> Optional[Severity]:
    """Return max severity across all findings, None if empty.

    Order: critical > high > medium > low > info
    """
    if not findings:
        return None

    best_rank = len(SEVERITY_ORDER)  # worse than any real severity
    best_severity = None

    for f in findings:
        sev_val = f.severity if isinstance(f.severity, Severity) else Severity(f.severity)
        rank = SEVERITY_RANK.get(sev_val, len(SEVERITY_ORDER))
        if rank < best_rank:
            best_rank = rank
            best_severity = sev_val

    return best_severity


def compute_finding_counts(
    findings: List[Union[Finding, FindingCreate]]
) -> dict:
    """Return {critical:N, high:N, medium:N, low:N, info:N}."""
    counts = {s.value: 0 for s in Severity}
    for f in findings:
        sev_val = f.severity if isinstance(f.severity, str) else f.severity.value
        if sev_val in counts:
            counts[sev_val] += 1
    return counts


def deduplicate_findings(
    findings: List[FindingCreate]
) -> List[FindingCreate]:
    """Deduplicate findings by (title.lower(), file_path or '').

    Keeps highest severity when duplicates are found.
    """
    seen: dict = {}  # key -> FindingCreate

    for f in findings:
        key = (f.title.lower().strip(), f.file_path or '')
        if key not in seen:
            seen[key] = f
        else:
            existing = seen[key]
            existing_sev = existing.severity if isinstance(existing.severity, Severity) else Severity(existing.severity)
            new_sev = f.severity if isinstance(f.severity, Severity) else Severity(f.severity)
            if SEVERITY_RANK.get(new_sev, 99) < SEVERITY_RANK.get(existing_sev, 99):
                seen[key] = f

    return list(seen.values())
