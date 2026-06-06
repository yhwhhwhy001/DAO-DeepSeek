"""Resource Engine — energy remnants from dead cells."""
from dataclasses import dataclass

REMNANT_DECAY_RATE = 0.05
ABSORPTION_MATRIX = {
    0: {0: 1.0, 1: 0.3, 2: 0.3, 3: 0.3},
    1: {0: 0.7, 1: 0.7, 2: 0.7, 3: 0.7},
    2: {0: 0.2, 1: 0.2, 2: 1.5, 3: 0.2},
    3: {0: 0.8, 1: 0.8, 2: 0.8, 3: 0.8},
}


@dataclass
class EnergyRemnant:
    x: int
    y: int
    energy: float
    type: int
    decay_rate: float = REMNANT_DECAY_RATE


def absorb_remnant(cell_type: int, remnant_type: int) -> float:
    return ABSORPTION_MATRIX.get(cell_type, {}).get(remnant_type, 0.5)


class ResourceEngine:
    def __init__(self):
        self._remnants: dict[tuple[int, int], EnergyRemnant] = {}

    def create(self, x: int, y: int, energy: float, remnant_type: int) -> None:
        self._remnants[(x, y)] = EnergyRemnant(x=x, y=y, energy=energy, type=remnant_type)

    def get(self, x: int, y: int) -> EnergyRemnant | None:
        return self._remnants.get((x, y))

    def absorb(self, x: int, y: int, cell_type: int, fraction: float = 1.0) -> float:
        r = self._remnants.get((x, y))
        if r is None:
            return 0.0
        efficiency = absorb_remnant(cell_type, r.type)
        absorbed = r.energy * fraction * efficiency
        r.energy -= r.energy * fraction
        if r.energy < 0.01:
            del self._remnants[(x, y)]
        return absorbed

    def decay_all(self) -> None:
        expired = []
        for pos, r in self._remnants.items():
            r.energy -= r.decay_rate
            if r.energy <= 0:
                expired.append(pos)
        for pos in expired:
            del self._remnants[pos]

    @property
    def all_remnants(self):
        return self._remnants.values()

    @property
    def count(self) -> int:
        return len(self._remnants)
