"""Tests for Myth Engine."""
from src.myth_engine import MythEngine, HeroLineage


class TestMythEngine:
    def test_generate_founder_narrative(self):
        eng = MythEngine()
        narrative = eng.generate_founder_narrative(
            civ_name="civ_0", founder="L1", born_at=100,
            region="top", competitor_count=3, mutualism_count=2,
            peak_tick=300, peak_size=10, peak_cells=50)
        assert "civ_0" in narrative and "L1" in narrative

    def test_empty_heroes(self):
        eng = MythEngine()
        assert eng.get_heroes() == []

    def test_belief_extraction(self):
        eng = MythEngine()
        eng.extract_beliefs("civ_0", [
            {"id": "know_1", "antecedent": "sym_A", "consequent": "sym_B",
             "confidence": 2.0, "generation_depth": 4, "lineage_count": 3}
        ])
        beliefs = eng.get_beliefs("civ_0")
        assert len(beliefs) >= 1

    def test_add_hero(self):
        eng = MythEngine()
        hero = HeroLineage(lineage_root="L1", peak_score=85.0, knowledge_count=3,
                          channel=1, max_generation=5)
        eng.add_hero("civ_0", hero)
        assert len(eng.get_heroes("civ_0")) == 1
