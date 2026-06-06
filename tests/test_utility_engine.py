"""Tests for Utility Engine."""
from src.utility_engine import UtilityEngine, compute_reward


class TestReward:
    def test_survival_bonus(self):
        r = compute_reward(energy_delta=0.0, survived=True, structure_joined=False,
                           structure_lost=False, near_death_recovery=False, signals_received=0)
        assert r == 0.1

    def test_energy_gain_positive(self):
        r = compute_reward(energy_delta=3.0, survived=True, structure_joined=False,
                           structure_lost=False, near_death_recovery=False, signals_received=0)
        assert r == 0.1 + 3.0 * 2.0

    def test_structure_joined_bonus(self):
        r = compute_reward(energy_delta=0.0, survived=True, structure_joined=True,
                           structure_lost=False, near_death_recovery=False, signals_received=0)
        assert r == 0.1 + 0.5

    def test_near_death_recovery(self):
        r = compute_reward(energy_delta=0.0, survived=True, structure_joined=False,
                           structure_lost=False, near_death_recovery=True, signals_received=3)
        assert r == 0.1 + 1.0 + 3 * 0.2


class TestUtilityEngine:
    def test_q_update_increases_for_positive_reward(self):
        eng = UtilityEngine()
        eng.update("s1", "MOVE_N", reward=2.0, next_state_key="s1", next_action="STAY")
        q = eng.get_q("s1", "MOVE_N")
        assert q > 0

    def test_q_inheritance_decays_values(self):
        eng = UtilityEngine()
        eng._q_table["s1"] = {"MOVE_N": 2.0, "STAY": -1.0}
        child = eng.create_inherited()
        assert child.get_q("s1", "MOVE_N") == 1.0
        assert child.get_q("s1", "STAY") == -0.5

    def test_empty_parent_no_inheritance(self):
        eng = UtilityEngine()
        child = eng.create_inherited()
        assert len(child._q_table) == 0

    def test_q_table_lru_eviction(self):
        eng = UtilityEngine(max_states=3)
        for i in range(5):
            eng.update(f"s{i}", "STAY", reward=0.1, next_state_key=f"s{i}", next_action="STAY")
        assert len(eng._q_table) <= 3
