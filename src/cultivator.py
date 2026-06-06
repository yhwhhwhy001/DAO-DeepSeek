"""修士引擎 —— 境界、法术、突破、轮回"""
import random
from dataclasses import dataclass

SPELL_COSTS = {"吐纳术": 0, "护体罡气": 5, "神念探查": 3, "血遁术": 15, "夺舍术": 50}
REALMS = [
    {"name": "练气", "min_energy": 0, "tribulation": 0.0, "max_skills": 1},
    {"name": "筑基", "min_energy": 10, "tribulation": 0.10, "max_skills": 2},
    {"name": "金丹", "min_energy": 30, "tribulation": 0.20, "max_skills": 2},
    {"name": "元婴", "min_energy": 60, "tribulation": 0.30, "max_skills": 3},
    {"name": "化神", "min_energy": 100, "tribulation": 0.40, "max_skills": 3},
    {"name": "渡劫", "min_energy": 200, "tribulation": 0.50, "max_skills": 4},
]


@dataclass
class Realm:
    name: str
    min_energy: float
    tribulation: float
    max_skills: int


class Cultivator:
    def __init__(self, cell_id: str):
        self.cell_id = cell_id
        self.energy = 10.0
        self.max_energy = 10.0
        self._realm_index = 0
        self.skills: list[str] = []
        self.shield_ticks = 0
        self.herbs = 0
        self.reincarnation_count = 0
        self.max_realm_reached = 0
        self.tick_age = 0
        self.total_kills = 0
        self.total_energy_absorbed = 0.0
        self._rng = random.Random()

    @property
    def realm(self) -> Realm:
        r = REALMS[self._realm_index]
        return Realm(**r)

    @property
    def max_skills(self) -> int:
        return self.realm.max_skills

    def cast(self, spell: str) -> bool:
        cost = SPELL_COSTS.get(spell, 0)
        if self.energy < cost:
            return False
        self.energy -= cost
        if spell == "护体罡气":
            self.shield_ticks = 10
        return True

    def try_breakthrough(self) -> bool:
        return breakthrough(self)

    def reincarnate(self, new_cell_id: str) -> "Cultivator":
        cv = Cultivator(new_cell_id)
        cv.energy = self.energy * 0.3 + 5.0
        cv.max_energy = cv.energy
        cv.skills = list(self.skills)
        cv.reincarnation_count = self.reincarnation_count + 1
        cv.max_realm_reached = max(self._realm_index, self.max_realm_reached)
        cv.total_kills = self.total_kills
        cv.total_energy_absorbed = self.total_energy_absorbed
        return cv


def breakthrough(cv: Cultivator, force_success=False, force_failure=False) -> bool:
    if cv._realm_index >= len(REALMS) - 1:
        return False
    next_realm = REALMS[cv._realm_index + 1]
    if cv.energy < next_realm["min_energy"]:
        return False
    prob = next_realm["tribulation"]
    if force_success:
        success = True
    elif force_failure:
        success = False
    else:
        success = cv._rng.random() > prob
    if success:
        cv._realm_index += 1
        cv.max_realm_reached = max(cv._realm_index, cv.max_realm_reached)
        return True
    else:
        cv.energy *= 0.5
        return False
