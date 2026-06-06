"""记忆引擎的测试。"""
from src.cell import Cell
from src.grid import Grid
from src.event_bus import EventBus, EventType
from src.structure_detector import StructureDetector
from src.memory_engine import MemoryEngine, Memory, MemorySnapshot, MemoryEvent


def make_grid(w=20, h=20):
    return Grid(width=w, height=h, boundary="toroidal")


class TestMemory:
    def test_memory_creation(self):
        m = Memory(structure_id="s1", generation=0, born_at=10)
        assert m.structure_id == "s1"
        assert m.generation == 0
        assert m.parent_id is None
        assert m.lineage_root == "s1"
        assert m.born_at == 10
        assert m.snapshots == []
        assert m.events == []

    def test_lineage_root_from_parent(self):
        m = Memory(structure_id="child", generation=1, parent_id="parent",
                   lineage_root="root_ancestor", born_at=50)
        assert m.lineage_root == "root_ancestor"

    def test_add_snapshot(self):
        m = Memory(structure_id="s1", generation=0, born_at=0)
        snap = MemorySnapshot(tick=5, cell_count=10, total_energy=25.0,
                              type_composition={1: 5, 2: 5}, shape_hash="abc", centroid=(5.0, 5.0))
        m.snapshots.append(snap)
        assert len(m.snapshots) == 1
        assert m.snapshots[0].tick == 5

    def test_add_event(self):
        m = Memory(structure_id="s1", generation=0, born_at=0)
        e = MemoryEvent(tick=10, event_type="fission", data={"child_id": "c1"})
        m.events.append(e)
        assert len(m.events) == 1
        assert m.events[0].event_type == "fission"


class TestMemoryEngine:
    def test_creates_memory_on_structure_formed(self):
        g = make_grid()
        bus = EventBus()
        det = StructureDetector(g, bus)
        eng = MemoryEngine(bus, det)

        g.place(Cell(x=5, y=5, id="a"))
        bus.tick = 1
        bus.publish(EventType.TICK_END, {"tick": 1, "alive_count": 1, "total_energy": 3.0})

        assert len(eng.memories) == 1
        m = list(eng.memories.values())[0]
        assert m.generation == 0
        assert m.born_at == 1

    def test_archives_memory_on_structure_lost(self):
        g = make_grid()
        bus = EventBus()
        det = StructureDetector(g, bus)
        eng = MemoryEngine(bus, det)

        g.place(Cell(x=5, y=5, id="a"))
        bus.tick = 1
        bus.publish(EventType.TICK_END, {"tick": 1, "alive_count": 1, "total_energy": 3.0})

        sid = list(eng.memories.keys())[0]
        g.remove(5, 5)
        for t in range(2, 5):
            bus.tick = t
            bus.publish(EventType.TICK_END, {"tick": t, "alive_count": 0, "total_energy": 0.0})

        assert sid not in eng.memories
        dead_ids = [m.structure_id for m in eng.dead_memories]
        assert sid in dead_ids

    def test_create_inherited(self):
        g = make_grid()
        bus = EventBus()
        det = StructureDetector(g, bus)
        eng = MemoryEngine(bus, det)

        child_m = eng.create_inherited("parent_1", "child_2", tick=50)
        assert child_m.structure_id == "child_2"
        assert child_m.parent_id == "parent_1"
        assert child_m.generation == 1
        assert child_m.born_at == 50

    def test_inherited_from_existing_parent(self):
        g = make_grid()
        bus = EventBus()
        det = StructureDetector(g, bus)
        eng = MemoryEngine(bus, det)

        g.place(Cell(x=5, y=5, id="a"))
        bus.tick = 1
        bus.publish(EventType.TICK_END, {"tick": 1, "alive_count": 1, "total_energy": 3.0})
        parent_id = list(eng.memories.keys())[0]

        child_m = eng.create_inherited(parent_id, "child_x", tick=50)
        assert child_m.parent_id == parent_id
        assert child_m.generation == 1
        assert child_m.lineage_root == parent_id

    def test_snapshots_collected_periodically(self):
        g = make_grid()
        bus = EventBus()
        det = StructureDetector(g, bus)
        eng = MemoryEngine(bus, det)

        g.place(Cell(x=5, y=5, id="a", energy=5.0))
        bus.tick = 5  # tick 5 triggers snapshot (5 % 5 == 0)
        bus.publish(EventType.TICK_END, {"tick": 5, "alive_count": 1, "total_energy": 5.0})

        sid = list(eng.memories.keys())[0]
        assert len(eng.memories[sid].snapshots) == 1
        assert eng.memories[sid].snapshots[0].tick == 5

    def test_get_lineage(self):
        g = make_grid()
        bus = EventBus()
        det = StructureDetector(g, bus)
        eng = MemoryEngine(bus, det)

        eng.memories["A"] = Memory(structure_id="A", generation=0, born_at=0, lineage_root="A")
        eng.memories["B"] = Memory(structure_id="B", generation=1, parent_id="A", born_at=50, lineage_root="A")
        eng.memories["C"] = Memory(structure_id="C", generation=2, parent_id="B", born_at=100, lineage_root="A")

        lineage = eng.get_lineage("C")
        assert len(lineage) == 3
        assert [m.structure_id for m in lineage] == ["A", "B", "C"]
