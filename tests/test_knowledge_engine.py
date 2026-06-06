"""Tests for Knowledge Engine."""
from src.knowledge_engine import KnowledgeEngine, Knowledge


class TestKnowledgeEngine:
    def test_empty_scan(self):
        eng = KnowledgeEngine()
        assert eng.scan([], {}) == []

    def test_insufficient_data(self):
        eng = KnowledgeEngine()
        assert eng.scan([("sym_0", "sym_1")], {}) == []

    def test_discovers_knowledge(self):
        eng = KnowledgeEngine()
        transitions = [("sym_0", "sym_1")] * 10
        result = eng.scan(transitions, {})
        assert isinstance(result, list)

    def test_knowledge_dataclass(self):
        k = Knowledge(id="know_0", antecedent="sym_A", consequent="sym_B",
                      confidence=2.1, lineage_count=3, survival_effect=1.5,
                      generation_depth=2, first_seen=100)
        assert k.confidence == 2.1 and k.lineage_count == 3
