"""符号引擎的测试。"""
from src.symbol_engine import SymbolEngine, state_similarity, Symbol


class TestStateSimilarity:
    def test_identical(self):
        assert state_similarity("1_2_0_1_2_0_1", "1_2_0_1_2_0_1") == 7
    def test_different(self):
        assert state_similarity("0_0_0_0_0_0_0", "2_2_2_2_2_2_2") == 0
    def test_partial(self):
        assert state_similarity("1_2_0_1_2_0_1", "1_2_0_1_2_1_2") == 5


class TestSymbolEngine:
    def test_empty_cluster(self):
        eng = SymbolEngine()
        assert eng.scan([]) == []

    def test_cluster_forms_symbol(self):
        eng = SymbolEngine()
        q_data = [
            ("1_2_0_1_2_0_1", "MOVE_N", 0.5),
            ("1_2_0_1_2_0_2", "MOVE_N", 0.3),
        ]
        symbols = eng.scan(q_data)
        assert len(symbols) >= 1
