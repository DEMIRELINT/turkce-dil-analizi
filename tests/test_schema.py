from dilanaliz.schema import (
    AnalysisResult,
    Finding,
    FindingType,
    LLMAnalysis,
    LLMFinding,
)


def test_llm_analysis_to_result_maps_fields():
    llm = LLMAnalysis(
        findings=[
            LLMFinding(
                type=FindingType.IMLA,
                excerpt="yanlız",
                explanation="Doğrusu 'yalnız'.",
                suggestion="yalnız",
                rule_id="IMLA-YALNIZ",
                confidence=0.9,
            )
        ]
    )
    result = llm.to_result()
    assert isinstance(result, AnalysisResult)
    assert len(result.findings) == 1
    f = result.findings[0]
    assert isinstance(f, Finding)
    assert f.rule_id == "IMLA-YALNIZ"
    # offset/üstveri LLM tarafından doldurulmaz
    assert f.start is None and f.end is None


def test_empty_findings_default():
    assert LLMAnalysis().to_result().findings == []


def test_finding_type_enum_values():
    assert {t.value for t in FindingType} == {
        "imla",
        "dil_bilgisi",
        "ton",
        "tutarlilik",
    }
