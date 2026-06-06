"""Ecology Engine — relationship detection and ecological network."""
from dataclasses import dataclass, field


@dataclass
class EcologyNode:
    structure_id: str
    primary_type: int = 0
    trophic_level: float = 0.0
    niche: str = "consumer"
    population: int = 0


@dataclass
class EcologyEdge:
    from_id: str
    to_id: str
    relationship: str
    strength: float = 0.0


@dataclass
class EcologyNetwork:
    nodes: dict[str, EcologyNode] = field(default_factory=dict)
    edges: list[EcologyEdge] = field(default_factory=list)
    tick: int = 0


def classify_niche(energy_gen: float, energy_con: float, remnant_ratio: float) -> str:
    if remnant_ratio > 0.5:
        return "decomposer"
    if energy_gen > energy_con:
        return "producer"
    return "consumer"


def _cell_region(cells: set) -> set:
    region = set(cells)
    for x, y in list(cells):
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                region.add((x + dx, y + dy))
    return region


class EcologyEngine:
    def __init__(self):
        self.networks: list[EcologyNetwork] = []

    def scan(self, structures: list[dict], resource_engine=None) -> EcologyNetwork:
        net = EcologyNetwork()
        if len(structures) < 2:
            return net

        for s in structures:
            net.nodes[s["id"]] = EcologyNode(
                structure_id=s["id"],
                primary_type=s.get("primary_type", 0),
                population=len(s.get("cells", set())),
            )

        struct_list = list(structures)
        for i in range(len(struct_list)):
            for j in range(i + 1, len(struct_list)):
                A = struct_list[i]
                B = struct_list[j]
                a_cells = set(A.get("cells", set()))
                b_cells = set(B.get("cells", set()))

                if not a_cells or not b_cells:
                    continue

                # Direct cell overlap → competition
                overlap_ratio = len(a_cells & b_cells) / min(len(a_cells), len(b_cells))
                if overlap_ratio > 0.3:
                    net.edges.append(EcologyEdge(
                        A["id"], B["id"], "competition", round(overlap_ratio, 2)))
                    continue

                # Check adjacency (expanded regions)
                a_region = _cell_region(a_cells)
                b_region = _cell_region(b_cells)
                adjacent = bool(a_region & b_region)
                if not adjacent:
                    continue

                # Same primary type + adjacent → competition
                if A.get("primary_type") == B.get("primary_type"):
                    net.edges.append(EcologyEdge(
                        A["id"], B["id"], "competition", 0.5))
                    continue

                # Different types + adjacent + old enough → mutualism
                if A.get("age", 0) > 50 and B.get("age", 0) > 50:
                    net.edges.append(EcologyEdge(
                        A["id"], B["id"], "mutualism",
                        round(min(A["age"], B["age"]) / 100, 2)))

        self.networks.append(net)
        return net
