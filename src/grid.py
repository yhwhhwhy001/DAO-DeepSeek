"""Grid -- 2D spatial container for cells with neighbor queries."""
import random
from src.cell import Cell


NEIGHBOR_OFFSETS = [
    (-1, -1), (0, -1), (1, -1),
    (-1,  0),          (1,  0),
    (-1,  1), (0,  1), (1,  1),
]


class Grid:
    def __init__(self, width: int, height: int, boundary: str = "toroidal"):
        self.width = width
        self.height = height
        self.boundary = boundary
        self._cells: dict[tuple[int, int], Cell] = {}

    @property
    def alive_count(self) -> int:
        return len(self._cells)

    @property
    def total_energy(self) -> float:
        return sum(c.energy for c in self._cells.values())

    @property
    def all_cells(self):
        return self._cells.values()

    def place(self, cell: Cell) -> None:
        self._cells[(cell.x, cell.y)] = cell

    def get(self, x: int, y: int) -> Cell | None:
        return self._cells.get((x, y))

    def remove(self, x: int, y: int) -> Cell | None:
        return self._cells.pop((x, y), None)

    def is_empty(self, x: int, y: int) -> bool:
        return (x, y) not in self._cells

    def _resolve(self, x: int, y: int) -> tuple[int, int] | None:
        if self.boundary == "toroidal":
            return (x % self.width, y % self.height)
        if 0 <= x < self.width and 0 <= y < self.height:
            return (x, y)
        return None

    def get_neighbors(self, x: int, y: int) -> list[Cell | None]:
        result: list[Cell | None] = []
        for dx, dy in NEIGHBOR_OFFSETS:
            resolved = self._resolve(x + dx, y + dy)
            if resolved is None:
                result.append(None)
            else:
                result.append(self.get(*resolved))
        return result

    def positions_around(self, x: int, y: int) -> list[tuple[int, int]]:
        result: list[tuple[int, int]] = []
        for dx, dy in NEIGHBOR_OFFSETS:
            resolved = self._resolve(x + dx, y + dy)
            if resolved is not None:
                result.append(resolved)
        return result

    def empty_positions_around(self, x: int, y: int) -> list[tuple[int, int]]:
        return [p for p in self.positions_around(x, y) if self.is_empty(*p)]

    def random_empty_position(self) -> tuple[int, int] | None:
        all_positions = {(x, y) for x in range(self.width) for y in range(self.height)}
        empty = list(all_positions - set(self._cells.keys()))
        return random.choice(empty) if empty else None
