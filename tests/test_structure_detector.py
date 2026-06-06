"""结构检测器的测试。"""
from src.cell import Cell
from src.grid import Grid
from src.event_bus import EventBus, EventType
from src.structure_detector import (
    StructureDetector, Component, Structure,
    extract_components, compute_bbox_iou, compute_shape_hash,
    STABILITY_AGE, MISSED_MAX,
)


def make_grid(w=20, h=20):
    return Grid(width=w, height=h, boundary="toroidal")


class TestComponentExtraction:
    def test_empty_grid(self):
        assert extract_components(make_grid(), 0) == []

    def test_single_cell(self):
        g = make_grid()
        g.place(Cell(x=5, y=5, id="c1"))
        comps = extract_components(g, 0)
        assert len(comps) == 1
        assert comps[0].cell_ids == {"c1"}
        assert comps[0].id == "0_0"

    def test_two_separated(self):
        g = make_grid()
        g.place(Cell(x=1, y=1, id="a"))
        g.place(Cell(x=10, y=10, id="b"))
        comps = extract_components(g, 5)
        assert len(comps) == 2
        assert {c.id for c in comps} == {"5_0", "5_1"}

    def test_adjacent_form_one_component(self):
        g = make_grid()
        g.place(Cell(x=5, y=5, id="a"))
        g.place(Cell(x=5, y=4, id="b"))
        comps = extract_components(g, 0)
        assert len(comps) == 1
        assert comps[0].cell_ids == {"a", "b"}

    def test_diagonal_adjacent(self):
        g = make_grid()
        g.place(Cell(x=5, y=5, id="a"))
        g.place(Cell(x=6, y=4, id="b"))
        assert len(extract_components(g, 0)) == 1

    def test_chain_of_three(self):
        g = make_grid()
        g.place(Cell(x=5, y=5, id="a"))
        g.place(Cell(x=6, y=5, id="b"))
        g.place(Cell(x=7, y=5, id="c"))
        comps = extract_components(g, 0)
        assert len(comps) == 1
        assert comps[0].cell_ids == {"a", "b", "c"}

    def test_component_has_centroid_and_bbox(self):
        g = make_grid()
        g.place(Cell(x=3, y=4, id="a"))
        comps = extract_components(g, 0)
        assert comps[0].centroid == (3.0, 4.0)
        assert comps[0].bbox == (3, 4, 3, 4)


class TestBBoxIoU:
    def test_identical(self):
        assert compute_bbox_iou((0, 0, 4, 4), (0, 0, 4, 4)) == 1.0

    def test_disjoint(self):
        assert compute_bbox_iou((0, 0, 2, 2), (10, 10, 12, 12)) == 0.0

    def test_partial(self):
        iou = compute_bbox_iou((0, 0, 4, 4), (2, 2, 6, 6))
        assert abs(iou - 9.0 / 41.0) < 0.01


class TestStructureDetector:
    def test_new_components_become_candidates(self):
        g = make_grid()
        bus = EventBus()
        det = StructureDetector(g, bus)
        g.place(Cell(x=5, y=5, id="a"))
        g.place(Cell(x=5, y=6, id="b"))
        bus.tick = 1
        bus.publish(EventType.TICK_END, {"tick": 1, "alive_count": 2, "total_energy": 6.0})
        assert len(det.structures) == 1
        assert det.structures[0].status == "candidate"
        assert det.structures[0].age == 1

    def test_persistent_tracks_across_ticks(self):
        g = make_grid()
        bus = EventBus()
        det = StructureDetector(g, bus)
        g.place(Cell(x=5, y=5, id="a"))
        g.place(Cell(x=5, y=6, id="b"))
        bus.tick = 1
        bus.publish(EventType.TICK_END, {"tick": 1, "alive_count": 2, "total_energy": 6.0})
        assert det.structures[0].age == 1
        bus.tick = 2
        bus.publish(EventType.TICK_END, {"tick": 2, "alive_count": 2, "total_energy": 6.0})
        assert det.structures[0].age == 2

    def test_becomes_stable_after_threshold(self):
        g = make_grid()
        bus = EventBus()
        det = StructureDetector(g, bus)
        g.place(Cell(x=5, y=5, id="a"))
        g.place(Cell(x=5, y=6, id="b"))
        for t in range(1, STABILITY_AGE + 1):
            bus.tick = t
            bus.publish(EventType.TICK_END, {"tick": t, "alive_count": 2, "total_energy": 6.0})
        assert det.structures[0].status == "stable"

    def test_dies_after_missed_ticks(self):
        g = make_grid()
        bus = EventBus()
        det = StructureDetector(g, bus)
        g.place(Cell(x=5, y=5, id="a"))
        bus.tick = 1
        bus.publish(EventType.TICK_END, {"tick": 1, "alive_count": 1, "total_energy": 3.0})
        g.remove(5, 5)
        for t in range(2, 2 + MISSED_MAX):
            bus.tick = t
            bus.publish(EventType.TICK_END, {"tick": t, "alive_count": 0, "total_energy": 0.0})
        assert det.structures[0].status == "dead"

    def test_emits_structure_stable_event(self):
        g = make_grid()
        bus = EventBus()
        det = StructureDetector(g, bus)
        stable_events = []
        bus.subscribe(EventType.STRUCTURE_STABLE, lambda e: stable_events.append(e.data))
        g.place(Cell(x=5, y=5, id="a"))
        g.place(Cell(x=5, y=6, id="b"))
        for t in range(1, STABILITY_AGE + 1):
            bus.tick = t
            bus.publish(EventType.TICK_END, {"tick": t, "alive_count": 2, "total_energy": 6.0})
        assert len(stable_events) == 1

    def test_get_active_excludes_dead(self):
        g = make_grid()
        bus = EventBus()
        det = StructureDetector(g, bus)
        g.place(Cell(x=5, y=5, id="a"))
        bus.tick = 1
        bus.publish(EventType.TICK_END, {"tick": 1, "alive_count": 1, "total_energy": 3.0})
        g.remove(5, 5)
        for t in range(2, 2 + MISSED_MAX):
            bus.tick = t
            bus.publish(EventType.TICK_END, {"tick": t, "alive_count": 0, "total_energy": 0.0})
        assert det.get_active() == []

    def test_shape_hash_computed(self):
        g = make_grid()
        bus = EventBus()
        det = StructureDetector(g, bus)
        g.place(Cell(x=5, y=5, id="a"))
        g.place(Cell(x=5, y=6, id="b"))
        bus.tick = 1
        bus.publish(EventType.TICK_END, {"tick": 1, "alive_count": 2, "total_energy": 6.0})
        assert len(det.structures[0].shape_hash) > 0

    def test_fission_detection_creates_child(self):
        g = make_grid()
        bus = EventBus()
        det = StructureDetector(g, bus)

        g.place(Cell(x=5, y=5, id="a"))
        g.place(Cell(x=5, y=6, id="b"))
        g.place(Cell(x=6, y=5, id="c"))
        g.place(Cell(x=6, y=6, id="d"))
        bus.tick = 1
        bus.publish(EventType.TICK_END, {"tick": 1, "alive_count": 4, "total_energy": 12.0})
        assert len(det.structures) == 1
        parent = det.structures[0]

        # Split: move 2 cells far away
        g.remove(5, 5)
        g.remove(5, 6)
        g.place(Cell(x=15, y=15, id="a"))
        g.place(Cell(x=15, y=16, id="b"))

        bus.tick = 2
        bus.publish(EventType.TICK_END, {"tick": 2, "alive_count": 4, "total_energy": 12.0})
        assert len(det.structures) == 2
        assert any(s.id == parent.id for s in det.structures)

    def test_fission_emits_event(self):
        g = make_grid()
        bus = EventBus()
        det = StructureDetector(g, bus)
        fission_events = []
        bus.subscribe(EventType.STRUCTURE_FISSION, lambda e: fission_events.append(e.data))

        g.place(Cell(x=5, y=5, id="a"))
        g.place(Cell(x=5, y=6, id="b"))
        g.place(Cell(x=6, y=5, id="c"))
        g.place(Cell(x=6, y=6, id="d"))
        bus.tick = 1
        bus.publish(EventType.TICK_END, {"tick": 1, "alive_count": 4, "total_energy": 12.0})

        g.remove(5, 5)
        g.remove(5, 6)
        g.place(Cell(x=15, y=15, id="a"))
        g.place(Cell(x=15, y=16, id="b"))
        bus.tick = 2
        bus.publish(EventType.TICK_END, {"tick": 2, "alive_count": 4, "total_energy": 12.0})

        assert len(fission_events) == 1
        assert "parent_id" in fission_events[0]
        assert "child_id" in fission_events[0]

    def test_no_fission_when_overlap_too_low(self):
        g = make_grid()
        bus = EventBus()
        det = StructureDetector(g, bus)

        g.place(Cell(x=5, y=5, id="a"))
        g.place(Cell(x=5, y=6, id="b"))
        bus.tick = 1
        bus.publish(EventType.TICK_END, {"tick": 1, "alive_count": 2, "total_energy": 6.0})
        assert len(det.structures) == 1

        g.place(Cell(x=15, y=15, id="x"))
        g.place(Cell(x=15, y=16, id="y"))
        bus.tick = 2
        bus.publish(EventType.TICK_END, {"tick": 2, "alive_count": 4, "total_energy": 12.0})

        assert len(det.structures) == 2
