"""地图引擎的测试。"""
from src.map_engine import MapEngine


class TestMapEngine:
    def test_top_half_multiplier(self):
        engine = MapEngine(height=40)
        assert engine.get_multiplier(0, 0) == 1.5
        assert engine.get_multiplier(0, 19) == 1.5

    def test_bottom_half_multiplier(self):
        engine = MapEngine(height=40)
        assert engine.get_multiplier(0, 20) == 0.5
        assert engine.get_multiplier(0, 39) == 0.5

    def test_boundary(self):
        engine = MapEngine(height=40)
        assert engine.get_multiplier(0, 19) == 1.5
        assert engine.get_multiplier(0, 20) == 0.5
