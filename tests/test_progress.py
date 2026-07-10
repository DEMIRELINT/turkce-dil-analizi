"""analyze_document'ın ilerleme yayını (API gerektirmez).

Geçiş-farkında sahte modelle çalışıp toplanan ProgressEvent'lerin sırasını,
stage'lerini ve current/total değerlerini doğrular.
"""

from dilanaliz.analyzer import Analyzer
from dilanaliz.progress import ProgressEvent
from dilanaliz.schema import LLMAnalysis

_EMPTY = LLMAnalysis(findings=[], spelling=[])


class _FakeRules:
    def get_context(self, text: str, purpose: str = "all") -> str:
        return "KURALLAR"


class _FakeStructured:
    def invoke(self, messages):  # tüm geçişler boş döner; ilgilendiğimiz akış
        return _EMPTY


class _FakeModel:
    def with_structured_output(self, schema, **kwargs):  # noqa: ARG002
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


def _parallel_analyzer(max_workers: int) -> Analyzer:
    return Analyzer(
        chat_model=_FakeModel(),
        rules_provider=_FakeRules(),
        model_id="test-model",
        cache=None,
        speller=None,
        max_workers=max_workers,
    )


def test_progress_stage_order_single_chunk():
    # Sıralı yol (max_workers=1). Her parça "başladı/bitti" iki olay yayar; belge
    # geneli tutarlılık da başladı/bitti olarak yayılır.
    events = _collect("Tek paragraf.", max_chars=3000)
    stages = [e.stage for e in events]
    assert stages == [
        "chunk", "chunk_start", "chunk_done",
        "consistency_start", "consistency_done", "finalize", "done",
    ]
    assert events[0].total == 1
    assert events[-1].stage == "done"


def test_progress_emits_start_and_done_per_chunk():
    # İki paragraf, küçük bütçe → iki parça → her parça için başladı + bitti.
    events = _collect("aaaa\n\nbbbb", max_chars=5)
    starts = [e for e in events if e.stage == "chunk_start"]
    dones = [e for e in events if e.stage == "chunk_done"]
    assert [e.current for e in starts] == [1, 2]  # sıralı yolda kimlik artan
    assert [e.current for e in dones] == [1, 2]
    assert all(e.total == 2 for e in starts + dones)
    # Her olayın insan-okur bir mesajı olmalı.
    assert all(e.message for e in events)


def test_progress_parallel_each_chunk_has_start_and_done():
    # Paralel yolda olaylar sırasız gelebilir; ama "chunk" başta, "finalize"/"done"
    # sonda; her parçanın kararlı kimliği (1..N) hem başladı hem bitti olayında geçer.
    events: list[ProgressEvent] = []
    analyzer = _parallel_analyzer(max_workers=4)
    analyzer.analyze_document("aaaa\n\nbbbb\n\ncccc", max_chars=5, progress=events.append)

    stages = [e.stage for e in events]
    assert stages[0] == "chunk"
    assert stages[-2:] == ["finalize", "done"]
    starts = {e.current for e in events if e.stage == "chunk_start"}
    dones = {e.current for e in events if e.stage == "chunk_done"}
    assert starts == {1, 2, 3} and dones == {1, 2, 3}
    assert sum(1 for e in events if e.stage == "consistency_start") == 1
    assert sum(1 for e in events if e.stage == "consistency_done") == 1


def test_progress_optional_no_callback_still_works():
    # progress=None → yayın yok, davranış değişmez (hata fırlatmaz).
    result = _analyzer().analyze_document("Kısa metin.")
    assert result.findings == []
