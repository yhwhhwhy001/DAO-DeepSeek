"""历史引擎的测试。"""
from src.history_engine import HistoryEngine, LineageHistory, HistoryEvent


class TestLineageHistory:
    def test_record_event(self):
        lh = LineageHistory(lineage_root="L1", born_tick=100)
        lh.record(HistoryEvent(tick=150, event_type="peak", data={"size": 10}))
        assert len(lh.key_events) == 1


class TestHistoryEngine:
    def test_record_lineage_event(self):
        eng = HistoryEngine()
        eng.record_lineage_event("L1", tick=100, event_type="founded", data={})
        assert "L1" in eng.lineages

    def test_record_era(self):
        eng = HistoryEngine()
        eng.record_era("civ_0", tick_start=100, tick_end=200, era_name="golden_age", size=15)
        assert "civ_0" in eng.civilizations

    def test_lineage_narrative(self):
        eng = HistoryEngine()
        eng.record_lineage_event("L1", tick=100, event_type="founded", data={})
        eng.record_lineage_event("L1", tick=200, event_type="peak", data={"size": 10})
        eng.lineages["L1"].max_generation = 3
        eng.lineages["L1"].died_tick = 250
        narrative = eng.get_lineage_narrative("L1")
        assert "L1" in narrative and "150" in narrative
