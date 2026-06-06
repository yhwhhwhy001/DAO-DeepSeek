"""Cell -- the fundamental unit of the DAO Genesis universe."""
from dataclasses import dataclass, field
from uuid import uuid4


@dataclass
class Cell:
    x: int
    y: int
    type: int = 0
    energy: float = 0.0
    id: str = field(default_factory=lambda: str(uuid4()))

    def __hash__(self) -> int:
        return hash(self.id)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Cell):
            return NotImplemented
        return self.id == other.id

    @property
    def is_alive(self) -> bool:
        return self.energy > 0.0

    @property
    def position(self) -> tuple[int, int]:
        return (self.x, self.y)
