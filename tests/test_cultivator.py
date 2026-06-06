"""修士引擎测试"""
from src.cultivator import Cultivator, breakthrough


class TestRealm:
    def test_start_at_qi_condensation(self):
        cv = Cultivator(cell_id="p1")
        assert cv.realm.name == "练气"
        assert cv.energy == 20.0

    def test_breakthrough_succeeds(self):
        cv = Cultivator(cell_id="p1")
        cv.energy = 30.0
        assert breakthrough(cv, force_success=True)
        assert cv.realm.name == "筑基"

    def test_breakthrough_fails(self):
        cv = Cultivator(cell_id="p1")
        cv.energy = 30.0
        assert not breakthrough(cv, force_failure=True)
        assert cv.energy < 30.0

    def test_reincarnation(self):
        cv = Cultivator(cell_id="p1")
        cv.skills = ["金灵诀", "混元诀"]
        cv.energy = 80.0
        new_cv = cv.reincarnate(new_cell_id="p2")
        assert new_cv.cell_id == "p2"
        assert new_cv.skills == ["金灵诀", "混元诀"]
        assert new_cv.energy == 80.0 * 0.3 + 5.0
        assert new_cv.realm.name == "练气"

    def test_spell_cost(self):
        cv = Cultivator(cell_id="p1")
        cv.energy = 30.0
        assert cv.cast("护体罡气")
        assert cv.energy == 25.0
        assert cv.shield_ticks == 10

    def test_skill_slots_by_realm(self):
        cv = Cultivator(cell_id="p1")
        assert cv.max_skills == 1
        cv.energy = 30.0
        breakthrough(cv, force_success=True)
        assert cv.max_skills == 2
