"""记忆引擎 —— 可继承的记忆，包含快照、事件和谱系追踪。"""
from dataclasses import dataclass, field
from src.event_bus import EventBus, EventType
from src.structure_detector import StructureDetector

SNAPSHOT_INTERVAL = 5
MAX_SNAPSHOTS = 200
MAX_EVENTS = 500


@dataclass
class MemorySnapshot:
    tick: int
    cell_count: int
    total_energy: float
    type_composition: dict[int, int]
    shape_hash: str
    centroid: tuple[float, float]


@dataclass
class MemoryEvent:
    tick: int
    event_type: str
    data: dict


@dataclass
class Memory:
    structure_id: str
    generation: int = 0
    parent_id: str | None = None
    lineage_root: str = ""
    born_at: int = 0
    died_at: int | None = None
    snapshot_interval: int = SNAPSHOT_INTERVAL
    snapshots: list[MemorySnapshot] = field(default_factory=list)
    events: list[MemoryEvent] = field(default_factory=list)
    fission_children: list[str] = field(default_factory=list)

    def __post_init__(self):
        if not self.lineage_root:
            self.lineage_root = self.structure_id


class MemoryEngine:
    def __init__(self, bus: EventBus, detector: StructureDetector):
        self.bus = bus
        self.detector = detector
        self.memories: dict[str, Memory] = {}
        self.dead_memories: list[Memory] = []

        bus.subscribe(EventType.TICK_END, self._on_tick_end)
        bus.subscribe(EventType.STRUCTURE_FORMED, self._on_structure_formed)
        bus.subscribe(EventType.STRUCTURE_LOST, self._on_structure_lost)
        bus.subscribe(EventType.STRUCTURE_FISSION, self._on_fission)

    def create_inherited(self, parent_id: str, child_id: str, tick: int) -> Memory:
        parent = self.memories.get(parent_id)
        if parent:
            gen = parent.generation + 1
            root = parent.lineage_root
        else:
            gen = 1
            root = child_id

        memory = Memory(
            structure_id=child_id,
            generation=gen,
            parent_id=parent_id,
            lineage_root=root,
            born_at=tick,
        )
        self.memories[child_id] = memory
        return memory

    def get_lineage(self, structure_id: str) -> list[Memory]:
        chain = []
        current_id = structure_id
        while current_id:
            m = self.memories.get(current_id)
            if not m:
                for dm in self.dead_memories:
                    if dm.structure_id == current_id:
                        m = dm
                        break
            if not m:
                break
            chain.append(m)
            current_id = m.parent_id
        return list(reversed(chain))

    def get_lineage_stats(self) -> dict:
        all_mems = list(self.memories.values()) + self.dead_memories
        if not all_mems:
            return {"generations": {}, "max_depth": 0, "total_lineages": 0}

        gen_stats: dict[int, dict] = {}
        for m in all_mems:
            g = m.generation
            if g not in gen_stats:
                gen_stats[g] = {"count": 0, "lifespans": [], "max_lifespan": 0}
            gen_stats[g]["count"] += 1
            lifespan = (m.died_at or 0) - m.born_at
            if lifespan > 0:
                gen_stats[g]["lifespans"].append(lifespan)
                if lifespan > gen_stats[g]["max_lifespan"]:
                    gen_stats[g]["max_lifespan"] = lifespan

        for g, stats in gen_stats.items():
            lifespans = stats["lifespans"]
            stats["mean_lifespan"] = sum(lifespans) / len(lifespans) if lifespans else 0
            del stats["lifespans"]

        max_depth = 0
        for m in all_mems:
            lineage = self.get_lineage(m.structure_id)
            if len(lineage) > max_depth:
                max_depth = len(lineage)

        founders = sum(1 for m in all_mems if m.generation == 0)

        return {
            "generations": gen_stats,
            "max_depth": max_depth,
            "total_lineages": founders,
        }

    def _on_structure_formed(self, event) -> None:
        sid = event.data["structure_id"]
        if sid not in self.memories:
            self.memories[sid] = Memory(
                structure_id=sid,
                generation=0,
                born_at=event.tick,
            )

    def _on_structure_lost(self, event) -> None:
        sid = event.data["structure_id"]
        if sid in self.memories:
            m = self.memories.pop(sid)
            m.died_at = event.tick
            self.dead_memories.append(m)

    def _on_fission(self, event) -> None:
        parent_id = event.data["parent_id"]
        child_id = event.data["child_id"]
        tick = event.data["tick"]

        if parent_id in self.memories:
            parent = self.memories[parent_id]
            parent.fission_children.append(child_id)
            parent.events.append(MemoryEvent(
                tick=tick, event_type="fission",
                data={"child_id": child_id},
            ))
            if len(parent.events) > MAX_EVENTS:
                parent.events = parent.events[-MAX_EVENTS:]

            self.create_inherited(parent_id, child_id, tick)

    def _on_tick_end(self, event) -> None:
        tick = event.data["tick"]
        if tick % SNAPSHOT_INTERVAL != 0:
            return

        for struct in self.detector.get_active():
            if struct.id not in self.memories:
                continue
            m = self.memories[struct.id]

            type_counts: dict[int, int] = {}
            total_e = 0.0
            for c in self.detector.grid.all_cells:
                if c.id in struct.cells:
                    type_counts[c.type] = type_counts.get(c.type, 0) + 1
                    total_e += c.energy

            snap = MemorySnapshot(
                tick=tick,
                cell_count=len(struct.cells),
                total_energy=total_e,
                type_composition=type_counts,
                shape_hash=struct.shape_hash,
                centroid=struct.centroid,
            )
            m.snapshots.append(snap)
            if len(m.snapshots) > MAX_SNAPSHOTS:
                m.snapshots = m.snapshots[-MAX_SNAPSHOTS:]

            # 事件检测
            if total_e < 1.0:
                m.events.append(MemoryEvent(tick=tick, event_type="near_death", data={"energy": total_e}))
            if len(m.snapshots) >= 10:
                recent_e = [s.total_energy for s in m.snapshots[-10:]]
                mean_e = sum(recent_e) / len(recent_e)
                if mean_e > 0 and total_e > 2 * mean_e:
                    m.events.append(MemoryEvent(tick=tick, event_type="energy_peak", data={"energy": total_e}))

            if len(m.events) > MAX_EVENTS:
                m.events = m.events[-MAX_EVENTS:]
