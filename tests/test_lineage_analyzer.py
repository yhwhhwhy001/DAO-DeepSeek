"""Tests for Lineage Analyzer."""
from src.memory_engine import Memory, MemorySnapshot
from src.lineage_analyzer import LineageAnalyzer


def make_memory(sid, gen=0, parent=None, root=None, born=0, died=None,
                snapshots=None):
    return Memory(
        structure_id=sid, generation=gen, parent_id=parent,
        lineage_root=root or sid, born_at=born, died_at=died,
        snapshots=snapshots or [],
    )


class TestLineageAnalyzer:
    def test_depth_computation(self):
        analyzer = LineageAnalyzer()
        memories = [
            make_memory("A", gen=0, born=0, died=50),
            make_memory("B", gen=1, parent="A", root="A", born=50, died=80),
            make_memory("C", gen=2, parent="B", root="A", born=80),
        ]
        stats = analyzer.analyze(memories, [])
        assert stats["max_depth"] == 3
        assert stats["total_lineages"] == 1

    def test_generation_stats(self):
        analyzer = LineageAnalyzer()
        memories = [
            make_memory("A", gen=0, born=0, died=30),
            make_memory("B", gen=0, born=10, died=50),
            make_memory("C", gen=1, parent="A", root="A", born=30, died=60),
        ]
        stats = analyzer.analyze(memories, [])
        gens = stats["generations"]
        assert gens[0]["count"] == 2
        assert gens[1]["count"] == 1

    def test_shape_inheritance(self):
        analyzer = LineageAnalyzer()
        snap_a = [MemorySnapshot(tick=t, cell_count=2, total_energy=5.0,
                                  type_composition={}, shape_hash="hashX", centroid=(0,0))
                   for t in range(0, 20, 5)]
        snap_b = [MemorySnapshot(tick=t, cell_count=2, total_energy=5.0,
                                  type_composition={}, shape_hash="hashX", centroid=(0,0))
                   for t in range(20, 40, 5)]
        memories = [
            make_memory("A", gen=0, born=0, died=20, snapshots=snap_a),
            make_memory("B", gen=1, parent="A", root="A", born=20, died=40, snapshots=snap_b),
        ]
        stats = analyzer.analyze(memories, [])
        shapes = stats["shape_inheritance"]
        assert "hashX" in shapes
        assert shapes["hashX"]["generations"] >= 2

    def test_lifespan_trend(self):
        analyzer = LineageAnalyzer()
        memories = [
            make_memory("A", gen=0, born=0, died=20),
            make_memory("B", gen=0, born=0, died=25),
            make_memory("C", gen=1, parent="A", root="A", born=20, died=60),
            make_memory("D", gen=2, parent="C", root="A", born=60, died=100),
        ]
        stats = analyzer.analyze(memories, [])
        means = [stats["generations"][g]["mean_lifespan"] for g in sorted(stats["generations"])]
        assert means[-1] > means[0]

    def test_empty_analyzer(self):
        analyzer = LineageAnalyzer()
        stats = analyzer.analyze([], [])
        assert stats["max_depth"] == 0
