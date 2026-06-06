"""文明引擎 —— 社区检测与文明追踪。"""
from dataclasses import dataclass, field
from src.event_bus import EventBus, EventType


@dataclass
class Civilization:
    id: str
    founder_lineage: str
    core_structure_id: str
    born_at: int
    died_at: int | None = None
    name: str = ""
    member_lineages: list[str] = field(default_factory=list)
    member_structures: list[str] = field(default_factory=list)
    peak_size: int = 0
    peak_tick: int = 0
    status: str = "emerging"
    shared_symbols: list[str] = field(default_factory=list)
    dominant_channel: int = 0
    era: str = "founding"
    size_history: list[int] = field(default_factory=list)

    def _update_era(self) -> None:
        if len(self.size_history) < 3:
            return
        recent = self.size_history[-3:]
        if all(recent[i] > recent[i-1] for i in range(1, len(recent))):
            self.era = "expanding"
        elif all(recent[i] < recent[i-1] for i in range(1, len(recent))):
            self.era = "declining"
        elif self.peak_size > 0 and self.size_history[-1] >= self.peak_size * 0.9:
            self.era = "golden_age"
        else:
            self.era = "stable"


class CivilizationEngine:
    def __init__(self, bus: EventBus | None = None):
        self.bus = bus
        self.civilizations: list[Civilization] = []
        self._next_id = 0

    def scan(self, ecology_network, symbol_data: dict, tick: int) -> list[Civilization]:
        if ecology_network is None or ecology_network.number_of_nodes() < 2:
            return []

        try:
            import networkx as nx
            communities = list(nx.connected_components(ecology_network))
        except ImportError:
            return []

        new_civs = []
        for community in communities:
            if len(community) < 2:
                continue
            lineages = set()
            for node in community:
                lineage = ecology_network.nodes[node].get("lineage_root", node)
                lineages.add(lineage)
            if len(lineages) < 2:
                continue

            core = max(community, key=lambda n: ecology_network.degree(n) if ecology_network.degree(n) > 0 else 1)
            founder = ecology_network.nodes[core].get("lineage_root", core)
            # 自动命名：根据 dominant type
            type_counts = {}
            for node in community:
                t = ecology_network.nodes[node].get("type", 0)
                type_counts[t] = type_counts.get(t, 0) + 1
            dom_type = max(type_counts, key=type_counts.get) if type_counts else 0
            type_names = {0: "金", 1: "火", 2: "木", 3: "水"}
            name = f"{type_names.get(dom_type, '?')}灵·{founder[:6]}"
            civ = Civilization(id=f"civ_{self._next_id}", founder_lineage=founder,
                             core_structure_id=core, born_at=tick,
                             member_lineages=list(lineages),
                             member_structures=list(community),
                             peak_size=len(lineages), peak_tick=tick)
            civ.name = name
            self._next_id += 1
            new_civs.append(civ)

        for new_civ in new_civs:
            matched = self._match_civilization(new_civ)
            if matched is None:
                self.civilizations.append(new_civ)
                if self.bus:
                    self.bus.publish(EventType.CIVILIZATION_BORN, {
                        "civilization_id": new_civ.id,
                        "founder": new_civ.founder_lineage,
                        "size": len(new_civ.member_lineages),
                    })

        for old_civ in self.civilizations:
            if old_civ.status == "fallen":
                continue
            old_civ.size_history.append(len(old_civ.member_lineages))
            if len(old_civ.size_history) > 20:
                old_civ.size_history = old_civ.size_history[-20:]
            old_civ._update_era()
            if len(old_civ.member_lineages) > old_civ.peak_size:
                old_civ.peak_size = len(old_civ.member_lineages)
                old_civ.peak_tick = tick

        return self.civilizations

    def _match_civilization(self, new_civ: Civilization) -> Civilization | None:
        for old_civ in self.civilizations:
            if old_civ.status == "fallen":
                continue
            old_set = set(old_civ.member_lineages)
            new_set = set(new_civ.member_lineages)
            if not old_set or not new_set:
                continue
            overlap = len(old_set & new_set) / len(old_set | new_set)
            if overlap >= 0.5:
                old_size = len(old_civ.member_lineages)
                old_civ.member_lineages = list(new_set | old_set)
                old_civ.member_structures = new_civ.member_structures
                new_size = len(old_civ.member_lineages)
                if self.bus and new_size > old_size:
                    self.bus.publish(EventType.CIVILIZATION_EXPANDED, {
                        "civilization_id": old_civ.id,
                        "new_lineage": list(new_set - old_set)[0] if new_set - old_set else "",
                        "size": new_size,
                    })
                return old_civ
        return None

    def mark_fallen(self, civ_id: str, tick: int) -> None:
        for civ in self.civilizations:
            if civ.id == civ_id and civ.status != "fallen":
                civ.status = "fallen"
                civ.died_at = tick
                if self.bus:
                    self.bus.publish(EventType.CIVILIZATION_FALLEN, {
                        "civilization_id": civ.id,
                        "peak_size": civ.peak_size,
                        "lifespan": tick - civ.born_at,
                    })
