import asyncio
import time
import json
import boto3
from app.config import settings
from app.services.diff_parser import parse_diff, diff_to_llm_context
from app.services.findings import (
    parse_llm_response,
    compute_overall_severity,
    compute_finding_counts,
    deduplicate_findings,
)
from app.models.finding import FindingCreate, Category, Severity
from typing import AsyncGenerator
import uuid

AGENT_PROMPTS = {
    Category.security: """You are a security expert reviewing a code diff. Look for:
- OWASP Top-10 vulnerabilities
- Injection attacks (SQL, command, LDAP, XPath)
- Broken auth/session management
- Sensitive data exposure (hardcoded secrets, PII logging, API keys)
- XXE, insecure deserialization, known-vulnerable patterns
- Missing input validation, path traversal, SSRF

For each finding return severity (critical/high/medium/low/info), file_path, line_start, line_end, title (concise, 1 line), explanation (2-4 sentences), suggested_fix (corrected code), why_it_matters (1 paragraph), cwe_id if applicable.

Respond with JSON only: {{"findings": [...]}}

Code diff:
{diff}""",

    Category.logic: """You are a software engineer reviewing a code diff for logic bugs. Look for:
- Off-by-one errors, null/undefined dereferences
- Race conditions, deadlocks
- Incorrect boolean logic, unreachable code
- Unhandled error paths, missing error propagation
- Incorrect algorithm implementation, missing edge cases
- Integer overflow, type confusion

Respond with JSON only: {{"findings": [...]}} where each finding has: severity, file_path, line_start, line_end, title, explanation, suggested_fix, why_it_matters.

Code diff:
{diff}""",

    Category.performance: """You are a performance engineer reviewing a code diff. Look for:
- N+1 query patterns
- Unnecessary loops inside loops (O(n²) or worse where avoidable)
- Missing database indexes (SQL queries)
- Memory leaks (unclosed resources, circular references, growing caches)
- Blocking I/O in async contexts
- Large object serialization, unnecessary deep copies
- Missing pagination on large result sets

Respond with JSON only: {{"findings": [...]}} where each finding has: severity (max high for performance), file_path, line_start, line_end, title, explanation, suggested_fix, why_it_matters.

Code diff:
{diff}""",

    Category.style: """You are a code quality reviewer. Look for maintainability/style issues:
- Functions longer than 50 lines
- Poor naming (single letters, misleading names, abbreviations)
- Code duplication that should be abstracted
- Missing error handling where clearly needed
- Inconsistent patterns with surrounding code
- Dead code, commented-out code
- Magic numbers/strings without named constants

All findings should have severity: low or info only.
Respond with JSON only: {{"findings": [...]}} where each finding has: severity, file_path, line_start, line_end, title, explanation, suggested_fix.

Code diff:
{diff}""",

    Category.maintainability: """You are a software architect reviewing a code diff. Look for:
- Tight coupling, violation of single responsibility
- Missing abstractions where complexity is growing
- Inconsistency with patterns evident in surrounding code
- Missing test coverage for new public functions/methods
- Missing documentation for public APIs
- Over-engineering or unnecessary complexity

Severity: max medium for maintainability issues.
Respond with JSON only: {{"findings": [...]}} where each finding has: severity, file_path, line_start, line_end, title, explanation, suggested_fix, why_it_matters.

Code diff:
{diff}""",
}


def _get_bedrock_client():
    return boto3.client(
        "bedrock-runtime",
        region_name=settings.AWS_REGION,
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID or None,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY or None,
    )


async def _invoke_bedrock(prompt: str, model_id: str) -> str:
    loop = asyncio.get_event_loop()

    def _call():
        client = _get_bedrock_client()
        body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 4096,
            "temperature": 0.1,
            "messages": [{"role": "user", "content": prompt}],
        }
        response = client.invoke_model(
            modelId=model_id,
            body=json.dumps(body),
            contentType="application/json",
            accept="application/json",
        )
        result = json.loads(response["body"].read())
        return result["content"][0]["text"]

    return await loop.run_in_executor(None, _call)


async def run_agent(
    category: Category, diff_context: str, timeout: int
) -> list[FindingCreate]:
    prompt = AGENT_PROMPTS[category].format(diff=diff_context)
    # Security/logic/performance use Sonnet 4.6; style/maintainability use Haiku (cheaper)
    model_id = (
        settings.BEDROCK_MODEL_SONNET
        if category in (Category.security, Category.logic, Category.performance)
        else settings.BEDROCK_MODEL_HAIKU
    )
    try:
        raw = await asyncio.wait_for(
            _invoke_bedrock(prompt, model_id),
            timeout=timeout,
        )
        return parse_llm_response(raw, category)
    except asyncio.TimeoutError:
        return [
            FindingCreate(
                category=category,
                severity=Severity.info,
                title=f"{category.value.capitalize()} analysis unavailable",
                explanation=(
                    f"The {category.value} analysis agent timed out after {timeout} seconds."
                ),
                suggested_fix=None,
                why_it_matters=None,
                cwe_id=None,
            )
        ]
    except Exception as e:
        return [
            FindingCreate(
                category=category,
                severity=Severity.info,
                title=f"{category.value.capitalize()} analysis error",
                explanation=f"Analysis failed: {str(e)[:200]}",
                suggested_fix=None,
                why_it_matters=None,
                cwe_id=None,
            )
        ]


async def run_review(
    diff_text: str, context: str | None = None
) -> tuple[list[FindingCreate], str]:
    hunks = parse_diff(diff_text)
    diff_context = diff_to_llm_context(hunks)
    if context:
        diff_context = f"PR Context: {context}\n\n{diff_context}"

    results = await asyncio.gather(
        run_agent(Category.security, diff_context, settings.REVIEW_TIMEOUT_SECONDS),
        run_agent(Category.logic, diff_context, settings.REVIEW_TIMEOUT_SECONDS),
        run_agent(Category.performance, diff_context, settings.REVIEW_TIMEOUT_SECONDS),
        run_agent(Category.style, diff_context, settings.REVIEW_TIMEOUT_SECONDS),
        run_agent(Category.maintainability, diff_context, settings.REVIEW_TIMEOUT_SECONDS),
    )

    all_findings: list[FindingCreate] = []
    for finding_list in results:
        all_findings.extend(finding_list)

    deduped = deduplicate_findings(all_findings)
    return deduped, settings.BEDROCK_MODEL_SONNET


async def stream_review(
    diff_text: str, context: str | None = None
) -> AsyncGenerator[str, None]:
    start_time = time.time()

    yield 'event: status\ndata: {"message": "Parsing diff..."}\n\n'

    hunks = parse_diff(diff_text)
    line_count = sum(len(h.added_lines) + len(h.removed_lines) for h in hunks)
    diff_context = diff_to_llm_context(hunks)
    if context:
        diff_context = f"PR Context: {context}\n\n{diff_context}"

    yield (
        f'event: status\ndata: {{"message": "Running 5 parallel analysis agents...", '
        f'"line_count": {line_count}}}\n\n'
    )

    categories = [
        Category.security,
        Category.logic,
        Category.performance,
        Category.style,
        Category.maintainability,
    ]
    category_names = ["security", "logic", "performance", "style", "maintainability"]

    task_list = [
        asyncio.create_task(
            run_agent(cat, diff_context, settings.REVIEW_TIMEOUT_SECONDS)
        )
        for cat in categories
    ]
    task_to_name = {task: name for task, name in zip(task_list, category_names)}

    all_findings: list[FindingCreate] = []
    completed = 0

    pending = set(task_list)
    while pending:
        done, pending = await asyncio.wait(pending, return_when=asyncio.FIRST_COMPLETED)
        for task in done:
            findings = task.result()
            completed += 1
            cat_name = task_to_name.get(task, "unknown")

            yield (
                f'event: status\ndata: {{"message": "Completed {cat_name} analysis '
                f'({completed}/5)"}}\n\n'
            )

            for f in findings:
                finding_id = str(uuid.uuid4())
                finding_dict = {
                    "id": finding_id,
                    "category": f.category if isinstance(f.category, str) else f.category.value,
                    "severity": f.severity if isinstance(f.severity, str) else f.severity.value,
                    "file_path": f.file_path,
                    "line_start": f.line_start,
                    "line_end": f.line_end,
                    "title": f.title,
                    "explanation": f.explanation,
                    "suggested_fix": f.suggested_fix,
                    "why_it_matters": f.why_it_matters,
                    "cwe_id": f.cwe_id,
                }
                yield f"event: finding\ndata: {json.dumps(finding_dict)}\n\n"
                all_findings.append(f)

    deduped = deduplicate_findings(all_findings)
    overall = compute_overall_severity(deduped)
    counts = compute_finding_counts(deduped)
    latency_ms = int((time.time() - start_time) * 1000)

    summary = {
        "overall_severity": overall.value if overall else "PASS",
        "finding_counts": counts,
        "model_used": settings.BEDROCK_MODEL_SONNET,
        "latency_ms": latency_ms,
        "line_count": line_count,
        "total_findings": len(deduped),
    }
    yield f"event: summary\ndata: {json.dumps(summary)}\n\n"
    yield "event: done\ndata: {}\n\n"
