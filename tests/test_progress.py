"""analyze_document'ın ilerleme yayını (API gerektirmez).

Geçiş-farkında sahte modelle çalışıp toplanan ProgressEvent'lerin sırasını,
stage'lerini ve current/total değerlerini doğrular.
"""

from dilanaliz.analyzer import Analyzer
from dilanaliz.progress import ProgressEvent
from dilanaliz.schema import LLMAnalysis

_EMPTY = LLMAnalysis(findings=[], spelling=[])


class _FakeRules:
    def get_context(self, text: str) -> str:
        return "KURALLAR"


class _FakeStructured:
    def invoke(self, messages):  # tüm geçişler boş döner; ilgilendiğimiz akış
        return _EMPTY


class _FakeModel:
    def with_structured_output(self, schema):  # noqa: ARG002
        return _FakeStructured()


def _analyzer() -> Analyzer:
    return Analyzer(
        chat_model=_FakeModel(),
        rules_provider=_FakeRules(),
        model_id="test-model",
        cache=None,
        speller=None,
    )


def _collect(source: str, max_chars: int) -> list[ProgressEvent]:
    events: list[ProgressEvent] = []
    _analyzer().analyze_document(source, max_chars=max_chars, progress=events.append)
    return events


def test_progress_stage_order_single_chunk():
    events = _collect("Tek paragraf.", max_chars=3000)
    stages = [e.stage for e in events]
    # chunk → (local, tone) ×1 → consistency → finalize → done
    assert stages == ["chunk", "local", "tone", "consistency", "finalize", "done"]
    assert events[0].total == 1
    assert events[-1].stage == "done"


def test_progress_emits_per_chunk():
    # İki paragraf, küçük bütçe → iki parça → her parça için local+tone.
    events = _collect("aaaa\n\nbbbb", max_chars=5)
    locals_ = [e for e in events if e.stage == "local"]
    tones = [e for e in events if e.stage == "tone"]
    assert len(locals_) == 2 and len(tones) == 2
    assert [e.current for e in locals_] == [1, 2]
    assert all(e.total == 2 for e in locals_)
    # Her olayın insan-okur bir mesajı olmalı.
    assert all(e.message for e in events)


def test_progress_optional_no_callback_still_works():
    # progress=None → yayın yok, davranış değişmez (hata fırlatmaz).
    result = _analyzer().analyze_document("Kısa metin.")
    assert result.findings == []
