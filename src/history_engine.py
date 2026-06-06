"""历史引擎 —— 三层事件记录与纪元检测。"""
from dataclasses import dataclass, field


@dataclass
class HistoryEvent:
    tick: int
    event_type: str
    data: dict


@dataclass
class LineageHistory:
    lineage_root: str
    born_tick: int
    died_tick: int | None = None
    max_generation: int = 0
    total_structures: int = 0
    key_events: list[HistoryEvent] = field(default_factory=list)

    def record(self, event: HistoryEvent) -> None:
        self.key_events.append(event)


@dataclass
class EraEvent:
    tick_start: int
    tick_end: int
    era_name: str
    size: int
    key_development: str = ""


@dataclass
class CivilizationHistory:
    civilization_id: str
    timeline: list[EraEvent] = field(default_factory=list)


class HistoryEngine:
    def __init__(self):
        self.lineages: dict[str, LineageHistory] = {}
        self.civilizations: dict[str, CivilizationHistory] = {}
        self.environmental: list[dict] = []

    def record_lineage_event(self, lineage_root: str, tick: int,
                             event_type: str, data: dict) -> None:
        if lineage_root not in self.lineages:
            self.lineages[lineage_root] = LineageHistory(lineage_root=lineage_root, born_tick=tick)
        self.lineages[lineage_root].record(HistoryEvent(tick=tick, event_type=event_type, data=data))

    def record_era(self, civ_id: str, tick_start: int, tick_end: int,
                   era_name: str, size: int, key_dev: str = "") -> None:
        if civ_id not in self.civilizations:
            self.civilizations[civ_id] = CivilizationHistory(civilization_id=civ_id)
        self.civilizations[civ_id].timeline.append(
            EraEvent(tick_start, tick_end, era_name, size, key_dev))

    def record_environment(self, tick: int, region: str,
                           remnant_count: int, cell_density: float) -> None:
        self.environmental.append({
            "tick": tick, "region": region,
            "remnant_count": remnant_count, "cell_density": cell_density,
        })

    def get_lineage_narrative(self, lineage_root: str) -> str:
        lh = self.lineages.get(lineage_root)
        if not lh:
            return ""
        events = [f"tick {e.tick}: {e.event_type}" for e in lh.key_events[-5:]]
        lifespan = (lh.died_tick or 0) - lh.born_tick
        return (f"Lineage {lineage_root}: born at {lh.born_tick}, "
                f"lived {lifespan} ticks, max gen {lh.max_generation}. "
                f"Recent: {' | '.join(events)}")
