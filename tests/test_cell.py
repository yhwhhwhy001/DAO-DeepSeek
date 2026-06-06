"""Cell 数据类的测试。"""
import uuid
from src.cell import Cell


class TestCell:
    def test_defaults(self):
        c = Cell(x=5, y=10)
        assert c.x == 5
        assert c.y == 10
        assert c.type == 0
        assert c.energy == 0.0
        uuid.UUID(c.id)

    def test_explicit_values(self):
        c = Cell(x=3, y=7, type=2, energy=5.5, id="test-id")
        assert c.type == 2
        assert c.energy == 5.5
        assert c.id == "test-id"

    def test_equality_by_id(self):
        c1 = Cell(x=0, y=0, id="same")
        c2 = Cell(x=10, y=20, id="same")
        c3 = Cell(x=0, y=0, id="diff")
        assert c1 == c2
        assert c1 != c3

    def test_hash_by_id(self):
        c1 = Cell(x=0, y=0, id="abc")
        c2 = Cell(x=10, y=20, id="abc")
        assert hash(c1) == hash(c2)
        assert len({c1, c2}) == 1

    def test_is_alive(self):
        assert Cell(x=0, y=0, energy=1.0).is_alive
        assert not Cell(x=0, y=1, energy=0.0).is_alive
        assert not Cell(x=0, y=2, energy=-0.5).is_alive

    def test_position_property(self):
        assert Cell(x=4, y=9).position == (4, 9)
