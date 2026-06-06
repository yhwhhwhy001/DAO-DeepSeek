"""修士引擎 —— 境界、法术、突破、轮回、功法"""
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

SKILL_PATTERNS = {
    "金灵诀":   {"desc": "type=0 残骸吸收 +50%",   "absorb_bonus": {0: 0.5},  "move_discount": 0, "damage_reduce": 0},
    "木灵诀":   {"desc": "type=1 残骸吸收 +50%",   "absorb_bonus": {1: 0.5},  "move_discount": 0, "damage_reduce": 0},
    "水灵诀":   {"desc": "type=2 残骸吸收 +50%",   "absorb_bonus": {2: 0.5},  "move_discount": 0, "damage_reduce": 0},
    "火灵诀":   {"desc": "type=3 残骸吸收 +50%",   "absorb_bonus": {3: 0.5},  "move_discount": 0, "damage_reduce": 0},
    "混元诀":   {"desc": "全类型吸收 +20%",         "absorb_bonus": {0:0.2,1:0.2,2:0.2,3:0.2}, "move_discount": 0, "damage_reduce": 0},
    "遁法真解": {"desc": "移动消耗 -50%",           "absorb_bonus": {},         "move_discount": 0.5, "damage_reduce": 0},
    "不灭金身": {"desc": "伤害减免 30%",             "absorb_bonus": {},         "move_discount": 0, "damage_reduce": 0.3},
}


@dataclass
class Realm:
    name: str
    min_energy: float
    tribulation: float
    max_skills: int


class Cultivator:
    def __init__(self, cell_id: str):
        self.cell_id = cell_id
        self.energy = 20.0
        self.max_energy = 20.0
        self._realm_index = 0
        self.skills: list[str] = []          # 已装备功法
        self.discovered_skills: list[str] = []  # 已发现可装备功法
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

    def equip_skill(self, name: str) -> bool:
        if name not in self.discovered_skills:
            return False
        if name in self.skills:
            return False
        if len(self.skills) >= self.max_skills:
            return False
        self.skills.append(name)
        return True

    def get_skill_buffs(self):
        absorb: dict[int, float] = {}
        move_discount = 0.0
        damage_reduce = 0.0
        for skill_name in self.skills:
            p = SKILL_PATTERNS.get(skill_name, {})
            for t, v in p.get("absorb_bonus", {}).items():
                absorb[t] = absorb.get(t, 0) + v
            move_discount += p.get("move_discount", 0)
            damage_reduce += p.get("damage_reduce", 0)
        return {"absorb_bonus": absorb, "move_discount": move_discount, "damage_reduce": damage_reduce}

    def reincarnate(self, new_cell_id: str) -> "Cultivator":
        cv = Cultivator(new_cell_id)
        cv.energy = self.energy * 0.3 + 5.0
        cv.max_energy = cv.energy
        cv.skills = list(self.skills)
        cv.discovered_skills = list(self.discovered_skills)
        cv.reincarnation_count = self.reincarnation_count + 1
        cv.max_realm_reached = max(self._realm_index, self.max_realm_reached)
        cv.total_kills = self.total_kills
        cv.total_energy_absorbed = self.total_energy_absorbed
        return cv


def discover_skill_from_knowledge(knowledge_antecedent: str, knowledge_consequent: str) -> str | None:
    """根据 Knowledge 的 antecedent/consequent 符号名尝试发现功法"""
    import random as _random
    candidates = []
    combined = (knowledge_antecedent + knowledge_consequent).lower()
    if "0" in knowledge_antecedent or "type" in combined[:10]:
        candidates.append("金灵诀")
    if "1" in knowledge_antecedent:
        candidates.append("木灵诀")
    if "2" in knowledge_antecedent:
        candidates.append("水灵诀")
    if "3" in knowledge_antecedent:
        candidates.append("火灵诀")
    candidates.append("混元诀")  # 总是可能发现
    if _random.random() < 0.5:
        candidates.append("遁法真解")
    if _random.random() < 0.3:
        candidates.append("不灭金身")
    return _random.choice(candidates) if candidates else None


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
