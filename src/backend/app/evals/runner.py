from __future__ import annotations

from app.evals.rules import evaluate_analysis_rules, evaluate_scoring_rules
from app.evals.types import EvalCase, EvalReport, EvalResult


def evaluate_case(case: EvalCase) -> EvalResult:
    findings = evaluate_analysis_rules(case.analysis)
    if case.score is not None:
        findings.extend(evaluate_scoring_rules(case.analysis, case.score))

    return EvalResult(
        case_id=case.case_id,
        passed=not any(finding.severity == "error" for finding in findings),
        findings=findings,
    )


def evaluate_cases(cases: list[EvalCase]) -> EvalReport:
    results = [evaluate_case(case) for case in cases]
    passed_cases = sum(1 for result in results if result.passed)
    return EvalReport(
        total_cases=len(results),
        passed_cases=passed_cases,
        failed_cases=len(results) - passed_cases,
        results=results,
    )
