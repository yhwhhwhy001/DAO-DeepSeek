"""Structure Detector -- extracts connected components and tracks them across ticks."""
import hashlib
from collections import deque
from dataclasses import dataclass, field
from src.grid import Grid
from src.event_bus import EventBus, EventType

STABILITY_AGE = 20
STABILITY_CV = 0.30
CELL_OVERLAP = 0.50
BBOX_IOU = 0.30
MISSED_MAX = 3
SHAPE_HASH_LEN = 12


@dataclass
class Component:
    id: str
    cell_ids: set[str]
    centroid: tuple[float, float]
    bbox: tuple[int, int, int, int]
    type_counts: dict[int, int]


@dataclass
class Structure:
    id: str
    age: int = 0
    cells: set[str] = field(default_factory=set)
    size_history: list[int] = field(default_factory=list)
    centroid: tuple[float, float] = (0.0, 0.0)
    bbox: tuple[int, int, int, int] = (0, 0, 0, 0)
    shape_hash: str = ""
    status: str = "candidate"
    born_at: int = 0
    last_seen_at: int = 0
    missed_ticks: int = 0


def extract_components(grid: Grid, tick: int) -> list[Component]:
    visited: set[str] = set()
    components: list[Component] = []

    for cell in grid.all_cells:
        if cell.id in visited:
            continue

        comp_cells = []
        queue = deque([cell])

        while queue:
            c = queue.popleft()
            if c.id in visited:
                continue
            visited.add(c.id)
            comp_cells.append(c)
            for n in grid.get_neighbors(c.x, c.y):
                if n is not None and n.id not in visited:
                    queue.append(n)

        cell_ids = {c.id for c in comp_cells}
        positions = [(c.x, c.y) for c in comp_cells]
        cx = sum(p[0] for p in positions) / len(positions)
        cy = sum(p[1] for p in positions) / len(positions)
        xs = [p[0] for p in positions]
        ys = [p[1] for p in positions]
        type_counts: dict[int, int] = {}
        for c in comp_cells:
            type_counts[c.type] = type_counts.get(c.type, 0) + 1

        components.append(Component(
            id=f"{tick}_{len(components)}",
            cell_ids=cell_ids,
            centroid=(cx, cy),
            bbox=(min(xs), min(ys), max(xs), max(ys)),
            type_counts=type_counts,
        ))

    return components


def compute_bbox_iou(a: tuple, b: tuple) -> float:
    inter_x1 = max(a[0], b[0])
    inter_y1 = max(a[1], b[1])
    inter_x2 = min(a[2], b[2])
    inter_y2 = min(a[3], b[3])
    if inter_x1 > inter_x2 or inter_y1 > inter_y2:
        return 0.0
    inter_area = (inter_x2 - inter_x1 + 1) * (inter_y2 - inter_y1 + 1)
    area_a = (a[2] - a[0] + 1) * (a[3] - a[1] + 1)
    area_b = (b[2] - b[0] + 1) * (b[3] - b[1] + 1)
    return inter_area / (area_a + area_b - inter_area)


def _cell_ids_to_positions(grid: Grid, cell_ids: set[str]) -> list[tuple[int, int]]:
    result = []
    for cell in grid.all_cells:
        if cell.id in cell_ids:
            result.append((cell.x, cell.y))
    return result


def compute_shape_hash(positions: list[tuple[int, int]], centroid: tuple[float, float]) -> str:
    rel = sorted((int(p[0] - centroid[0]), int(p[1] - centroid[1])) for p in positions)
    key = repr(rel).encode()
    return hashlib.sha256(key).hexdigest()[:SHAPE_HASH_LEN]


class StructureDetector:
    def __init__(self, grid: Grid, bus: EventBus):
        self.grid = grid
        self.bus = bus
        self.structures: list[Structure] = []
        bus.subscribe(EventType.TICK_END, self._on_tick_end)

    @property
    def stable_count(self) -> int:
        return sum(1 for s in self.structures if s.status == "stable")

    @property
    def active_count(self) -> int:
        return sum(1 for s in self.structures if s.status != "dead")

    def get_active(self) -> list[Structure]:
        return [s for s in self.structures if s.status != "dead"]

    def get_stable(self) -> list[Structure]:
        return [s for s in self.structures if s.status == "stable"]

    def _on_tick_end(self, event) -> None:
        tick = event.data["tick"]
        components = extract_components(self.grid, tick)
        self._match(components, tick)

    def _match(self, components: list[Component], tick: int) -> None:
        unmatched = list(components)

        # --- Fission detection ---
        for struct in self.structures:
            if struct.status == "dead":
                continue
            if len(unmatched) < 2:
                continue

            overlapping = []
            for comp in unmatched:
                denom = max(len(struct.cells), len(comp.cell_ids), 1)
                overlap = len(struct.cells & comp.cell_ids) / denom
                if overlap > 0:
                    overlapping.append((comp, overlap))

            if len(overlapping) < 2:
                continue

            found_fission = False
            for i in range(len(overlapping)):
                if found_fission:
                    break
                for j in range(i + 1, len(overlapping)):
                    c1, _ = overlapping[i]
                    c2, _ = overlapping[j]
                    if c1.cell_ids & c2.cell_ids:
                        continue
                    combined = c1.cell_ids | c2.cell_ids
                    combined_overlap = len(struct.cells & combined) / max(len(struct.cells), len(combined))
                    if combined_overlap >= 0.60:
                        if len(c1.cell_ids) >= len(c2.cell_ids):
                            parent_comp, child_comp = c1, c2
                        else:
                            parent_comp, child_comp = c2, c1

                        self._update(struct, parent_comp, tick)
                        unmatched.remove(parent_comp)
                        unmatched.remove(child_comp)

                        positions = _cell_ids_to_positions(self.grid, child_comp.cell_ids)
                        shape_hash = compute_shape_hash(positions, child_comp.centroid) if positions else ""
                        child_struct = Structure(
                            id=child_comp.id,
                            age=1,
                            cells=child_comp.cell_ids,
                            size_history=[len(child_comp.cell_ids)],
                            centroid=child_comp.centroid,
                            bbox=child_comp.bbox,
                            shape_hash=shape_hash,
                            status="candidate",
                            born_at=tick,
                            last_seen_at=tick,
                            missed_ticks=0,
                        )
                        self.structures.append(child_struct)
                        self.bus.publish(EventType.STRUCTURE_FORMED, {
                            "structure_id": child_struct.id,
                            "component_id": child_comp.id,
                            "cell_count": len(child_comp.cell_ids),
                        })
                        self.bus.publish(EventType.STRUCTURE_FISSION, {
                            "parent_id": struct.id,
                            "child_id": child_struct.id,
                            "tick": tick,
                        })
                        found_fission = True
                        break
        # --- End fission detection ---

        for struct in self.structures:
            if struct.status == "dead":
                continue

            best_comp = None
            best_overlap = 0.0
            for comp in unmatched:
                denom = max(len(struct.cells), len(comp.cell_ids), 1)
                overlap = len(struct.cells & comp.cell_ids) / denom
                if overlap > best_overlap:
                    best_overlap = overlap
                    best_comp = comp

            if best_comp is None:
                struct.missed_ticks += 1
                continue

            if best_overlap >= CELL_OVERLAP:
                self._update(struct, best_comp, tick)
                unmatched.remove(best_comp)
                continue

            iou = compute_bbox_iou(struct.bbox, best_comp.bbox)
            if iou >= BBOX_IOU:
                self._update(struct, best_comp, tick)
                unmatched.remove(best_comp)
                continue

            struct.missed_ticks += 1

        for struct in self.structures:
            if struct.missed_ticks >= MISSED_MAX and struct.status != "dead":
                struct.status = "dead"
                self.bus.publish(EventType.STRUCTURE_LOST, {
                    "structure_id": struct.id, "age": struct.age, "reason": "missing",
                })

        for comp in unmatched:
            positions = _cell_ids_to_positions(self.grid, comp.cell_ids)
            shape_hash = compute_shape_hash(positions, comp.centroid) if positions else ""
            struct = Structure(
                id=comp.id,
                age=1,
                cells=comp.cell_ids,
                size_history=[len(comp.cell_ids)],
                centroid=comp.centroid,
                bbox=comp.bbox,
                shape_hash=shape_hash,
                status="candidate",
                born_at=tick,
                last_seen_at=tick,
                missed_ticks=0,
            )
            self.structures.append(struct)
            self.bus.publish(EventType.STRUCTURE_FORMED, {
                "structure_id": struct.id, "component_id": comp.id,
                "cell_count": len(comp.cell_ids),
            })

    def _update(self, struct: Structure, comp: Component, tick: int) -> None:
        struct.cells = comp.cell_ids
        struct.age += 1
        struct.last_seen_at = tick
        struct.missed_ticks = 0
        struct.centroid = comp.centroid
        struct.bbox = comp.bbox
        struct.size_history.append(len(comp.cell_ids))
        if len(struct.size_history) > 100:
            struct.size_history = struct.size_history[-100:]

        positions = _cell_ids_to_positions(self.grid, comp.cell_ids)
        if positions:
            struct.shape_hash = compute_shape_hash(positions, comp.centroid)

        if struct.status == "candidate" and self._is_stable(struct):
            struct.status = "stable"
            self.bus.publish(EventType.STRUCTURE_STABLE, {
                "structure_id": struct.id, "age": struct.age,
                "shape_hash": struct.shape_hash,
            })

    def _is_stable(self, struct: Structure) -> bool:
        if struct.age < STABILITY_AGE:
            return False
        recent = struct.size_history[-10:]  # sliding window
        if len(recent) < 2:
            return True
        mean = sum(recent) / len(recent)
        if mean == 0:
            return True
        variance = sum((s - mean) ** 2 for s in recent) / len(recent)
        return (variance ** 0.5) / mean < STABILITY_CV
