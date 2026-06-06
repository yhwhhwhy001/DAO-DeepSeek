"""语言引擎的测试。"""
from src.language_engine import LanguageEngine, build_signal


class TestSignal:
    def test_build_signal(self):
        sig = build_signal(channel=2, symbols=["sym_0", "sym_1", "sym_2"])
        assert sig["channel"] == 2 and len(sig["symbols"]) == 3

    def test_signal_truncates(self):
        sig = build_signal(channel=0, symbols=["a", "b", "c", "d", "e"])
        assert len(sig["symbols"]) == 3 and sig["symbols"] == ["c", "d", "e"]


class TestLanguageEngine:
    def test_record_signal(self):
        eng = LanguageEngine()
        eng.record_send("a", "b", channel=1, symbols=["sym_0"], same_lineage=True)
        stats = eng.get_stats()
        assert stats["total_signals"] == 1 and stats["cross_lineage"] == 0

    def test_stats_empty(self):
        eng = LanguageEngine()
        assert eng.get_stats()["total_signals"] == 0
