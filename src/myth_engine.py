"""Myth Engine — founder narratives, hero lineages, and belief systems."""
from dataclasses import dataclass, field


@dataclass
class HeroLineage:
    lineage_root: str
    peak_score: float = 0.0
    knowledge_count: int = 0
    channel: int = 0
    max_generation: int = 0


@dataclass
class BeliefTenet:
    knowledge_id: str
    formulation: str
    confidence: float
    believer_count: int
    first_seen: int = 0
    last_seen: int = 0


class MythEngine:
    def __init__(self):
        self.heroes: dict[str, list[HeroLineage]] = {}
        self.beliefs: dict[str, list[BeliefTenet]] = {}
        self.narratives: dict[str, dict] = {}

    def generate_founder_narrative(self, **kwargs) -> str:
        return (
            f"{kwargs.get('civ_name', 'Unknown')} was founded by "
            f"{kwargs.get('founder', 'Unknown')} at tick {kwargs.get('born_at', 0)} "
            f"in the {kwargs.get('region', 'Unknown')} region. "
            f"It rose amidst {kwargs.get('competitor_count', 0)} rivals "
            f"and formed {kwargs.get('mutualism_count', 0)} alliances. "
            f"At its peak (tick {kwargs.get('peak_tick', 0)}), "
            f"it encompassed {kwargs.get('peak_size', 0)} lineages "
            f"with {kwargs.get('peak_cells', 0)} cells."
        )

    def extract_beliefs(self, civ_id: str, knowledge_items: list[dict]) -> None:
        tenets = []
        for k in knowledge_items:
            if k.get("generation_depth", 0) >= 3:
                tenets.append(BeliefTenet(
                    knowledge_id=k["id"],
                    formulation=f"{k['antecedent']} leads to {k['consequent']}",
                    confidence=k.get("confidence", 0.0),
                    believer_count=k.get("lineage_count", 0),
                ))
        tenets.sort(key=lambda t: t.believer_count * t.confidence, reverse=True)
        self.beliefs[civ_id] = tenets

    def add_hero(self, civ_id: str, hero: HeroLineage) -> None:
        if civ_id not in self.heroes:
            self.heroes[civ_id] = []
        self.heroes[civ_id].append(hero)

    def get_heroes(self, civ_id: str = None) -> list[HeroLineage]:
        if civ_id:
            return self.heroes.get(civ_id, [])
        return [h for heroes in self.heroes.values() for h in heroes]

    def get_beliefs(self, civ_id: str) -> list[BeliefTenet]:
        return self.beliefs.get(civ_id, [])
