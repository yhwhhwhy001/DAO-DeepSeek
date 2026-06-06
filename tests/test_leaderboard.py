"""Tests for Leaderboard."""
from src.leaderboard import build_leaderboard, score_structure


class TestScoreStructure:
    def test_max_values_score_one(self):
        s = score_structure(100, 100, 20, 20, 4, 4, 10, 10)
        assert abs(s - 1.0) < 0.001

    def test_min_values_score_low(self):
        s = score_structure(0, 100, 0, 20, 0, 4, 0, 10)
        assert s < 0.3

    def test_range_zero_to_one(self):
        s = score_structure(50, 200, 10, 20, 2, 4, 5, 10)
        assert 0.0 <= s <= 1.0


class TestBuildLeaderboard:
    def test_returns_top_n_sorted(self):
        structs = [
            {"id": "a", "age": 100, "size": 10, "type_count": 3, "shape_hash": "h1"},
            {"id": "b", "age": 50,  "size": 5,  "type_count": 1, "shape_hash": "h2"},
            {"id": "c", "age": 200, "size": 20, "type_count": 4, "shape_hash": "h1"},
        ]
        pattern_occs = {"h1": 10, "h2": 3}
        ranked = build_leaderboard(structs, pattern_occs, num_types=4, top_n=2)
        assert len(ranked) == 2
        assert ranked[0]["id"] == "c"
        assert "score" in ranked[0]
        assert ranked[0]["score"] >= ranked[1]["score"]

    def test_empty_returns_empty(self):
        assert build_leaderboard([], {}, num_types=4) == []

    def test_missing_pattern_keys(self):
        structs = [{"id": "a", "age": 50, "size": 5, "type_count": 1, "shape_hash": "unknown"}]
        ranked = build_leaderboard(structs, {}, num_types=4, top_n=5)
        assert len(ranked) == 1
        assert 0.0 <= ranked[0]["score"] <= 1.0
