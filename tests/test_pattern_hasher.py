"""模式哈希器的测试。"""
from src.pattern_hasher import PatternHasher, compute_shape_hash


class TestShapeHash:
    def test_same_shape_same_hash(self):
        h1 = compute_shape_hash([(0, 0), (0, 1), (1, 0)], (0, 0))
        h2 = compute_shape_hash([(5, 5), (5, 6), (6, 5)], (5, 5))
        assert h1 == h2

    def test_different_shape_different_hash(self):
        h1 = compute_shape_hash([(0, 0), (0, 1)], (0, 0))
        h2 = compute_shape_hash([(0, 0), (1, 1)], (0, 0))
        assert h1 != h2

    def test_hash_length_is_12(self):
        h = compute_shape_hash([(0, 0), (1, 1)], (0, 0))
        assert len(h) == 12


class TestPatternHasher:
    def test_registers_new_pattern(self):
        ph = PatternHasher()
        ph.register("abc123", 0, (5, 5))
        assert len(ph.patterns) == 1
        assert ph.patterns["abc123"].total_occurrences == 1

    def test_increments_existing(self):
        ph = PatternHasher()
        ph.register("abc", 0, (1, 1))
        ph.register("abc", 5, (10, 10))
        assert ph.patterns["abc"].total_occurrences == 2
        assert len(ph.patterns["abc"].locations) == 2

    def test_ignores_empty_hash(self):
        ph = PatternHasher()
        ph.register("", 0, (0, 0))
        assert len(ph.patterns) == 0

    def test_get_top_returns_sorted(self):
        ph = PatternHasher()
        ph.register("a", 0, (0, 0))
        ph.register("a", 1, (1, 1))
        ph.register("a", 2, (2, 2))
        ph.register("b", 0, (5, 5))
        ph.register("c", 0, (9, 9))
        ph.register("c", 1, (8, 8))
        top = ph.get_top(2)
        assert len(top) == 2
        assert top[0][0] == "a"
        assert top[0][1] == 3

    def test_unique_count(self):
        ph = PatternHasher()
        ph.register("a", 0, (0, 0))
        ph.register("b", 0, (1, 1))
        ph.register("a", 1, (2, 2))
        assert ph.unique_count() == 2
