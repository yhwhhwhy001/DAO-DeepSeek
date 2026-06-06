"""资源引擎的测试。"""
from src.resource_engine import ResourceEngine, absorb_remnant


class TestAbsorption:
    def test_specialist_absorption(self):
        assert absorb_remnant(cell_type=0, remnant_type=0) == 1.0
    def test_cross_type_absorption(self):
        assert absorb_remnant(cell_type=0, remnant_type=1) == 0.3
    def test_generalist_absorption(self):
        for rt in range(4):
            assert absorb_remnant(cell_type=1, remnant_type=rt) == 0.7


class TestResourceEngine:
    def test_create_remnant(self):
        eng = ResourceEngine()
        eng.create(5, 10, energy=3.0, remnant_type=2)
        r = eng.get(5, 10)
        assert r is not None and r.energy == 3.0 and r.type == 2

    def test_absorb_full(self):
        eng = ResourceEngine()
        eng.create(5, 10, energy=3.0, remnant_type=1)
        absorbed = eng.absorb(5, 10, cell_type=0, fraction=1.0)
        assert absorbed > 0
        assert eng.get(5, 10) is None

    def test_absorb_partial(self):
        eng = ResourceEngine()
        eng.create(5, 10, energy=4.0, remnant_type=0)
        absorbed = eng.absorb(5, 10, cell_type=0, fraction=0.5)
        assert absorbed > 0
        remaining = eng.get(5, 10)
        assert remaining is not None and remaining.energy < 4.0

    def test_decay_removes_expired(self):
        eng = ResourceEngine()
        eng.create(5, 10, energy=0.008, remnant_type=0)
        eng.decay_all()
        assert eng.get(5, 10) is None

    def test_empty_position(self):
        eng = ResourceEngine()
        assert eng.get(99, 99) is None
        assert eng.absorb(99, 99, 0, 1.0) == 0.0
