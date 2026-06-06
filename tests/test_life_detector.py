"""Tests for Life Detector."""
from src.life_detector import LifeDetector, compute_survival_score, compute_memory_score


class TestSurvivalScore:
    def test_young_structure_low_score(self):
        s = compute_survival_score(age=5, is_stable=False, generation=0)
        assert s < 10

    def test_old_stable_high_score(self):
        s = compute_survival_score(age=150, is_stable=True, generation=3)
        assert s >= 15


class TestMemoryScore:
    def test_rich_memory_high_score(self):
        m = {"snapshot_count": 60, "event_types": 4, "has_parent": True, "has_children": True}
        s = compute_memory_score(m)
        assert s >= 15

    def test_empty_memory_low_score(self):
        m = {"snapshot_count": 0, "event_types": 0, "has_parent": False, "has_children": False}
        s = compute_memory_score(m)
        assert s < 5


class TestLifeDetector:
    def test_inert_below_60(self):
        det = LifeDetector()
        result = det.assess("s1", age=10, is_stable=False, generation=0,
                            memory_data={"snapshot_count": 5, "event_types": 1,
                                         "has_parent": False, "has_children": False,
                                         "parent_id": None, "fission_children": [],
                                         "lineage_root": "s1"},
                            decision_data={"total_actions": 10, "non_stay": 1,
                                           "q_entries": 0, "unique_actions": 1},
                            adaptation_data={"snapshots": [], "events": []})
        assert result["classification"] == "inert"

    def test_proto_lifeform(self):
        det = LifeDetector()
        result = det.assess("s1", age=80, is_stable=True, generation=2,
                            memory_data={"snapshot_count": 40, "event_types": 3,
                                         "has_parent": True, "has_children": True,
                                         "parent_id": "p1", "fission_children": ["c1", "c2"],
                                         "lineage_root": "root"},
                            decision_data={"total_actions": 50, "non_stay": 20,
                                           "q_entries": 15, "unique_actions": 3},
                            adaptation_data={"snapshots": [{"total_energy": 10.0}] * 10,
                                             "events": []})
        assert result["classification"] in ("proto-lifeform", "true-lifeform")
        assert result["total_score"] >= 60

    def test_all_scores_in_range(self):
        det = LifeDetector()
        result = det.assess("s1", age=50, is_stable=True, generation=1,
                            memory_data={"snapshot_count": 20, "event_types": 2,
                                         "has_parent": True, "has_children": False,
                                         "parent_id": "p1", "fission_children": [],
                                         "lineage_root": "p1"},
                            decision_data={"total_actions": 30, "non_stay": 5,
                                           "q_entries": 5, "unique_actions": 2},
                            adaptation_data={"snapshots": [{"total_energy": 5.0}] * 5,
                                             "events": []})
        for dim in ["survival", "memory", "replication", "decision", "adaptation"]:
            assert 0 <= result["scores"][dim] <= 20
