"""文明引擎的测试。"""
from src.civilization_engine import CivilizationEngine, Civilization


class TestCivilization:
    def test_civilization_creation(self):
        c = Civilization(id="civ_0", founder_lineage="root_A", core_structure_id="s1", born_at=100)
        assert c.status == "emerging" and c.founder_lineage == "root_A"

    def test_era_transition(self):
        c = Civilization(id="civ_0", founder_lineage="root_A", core_structure_id="s1", born_at=100)
        c.size_history = [3, 5, 8, 10]
        c._update_era()
        assert c.era == "expanding"


class TestCivilizationEngine:
    def test_empty_scan(self):
        eng = CivilizationEngine()
        assert eng.scan(None, {}, 100) == []

    def test_cross_tick_matching(self):
        eng = CivilizationEngine()
        old = Civilization(id="civ_0", founder_lineage="L1", core_structure_id="s1", born_at=100)
        old.member_lineages = ["L1", "L2", "L3"]
        eng.civilizations = [old]
        new = Civilization(id="civ_1", founder_lineage="L1", core_structure_id="s1", born_at=200)
        new.member_lineages = ["L1", "L2", "L4"]
        matched = eng._match_civilization(new)
        assert matched is not None
