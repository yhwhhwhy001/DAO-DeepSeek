"""CLI Renderer — Rich-based terminal display of the universe."""
from rich.live import Live
from rich.panel import Panel
from rich.layout import Layout
from rich.console import Console
from src.grid import Grid
from src.event_bus import EventBus, EventType


TYPE_CHARS = {0: "·", 1: "○", 2: "◇", 3: "□"}


def make_grid_display(grid: Grid, width: int, height: int) -> str:
    lines = []
    for y in range(height):
        row = []
        for x in range(width):
            cell = grid.get(x, y)
            row.append(TYPE_CHARS.get(cell.type, "?") if cell else " ")
        lines.append("".join(row))
    return "\n".join(lines)


class Renderer:
    def __init__(self, grid: Grid, bus: EventBus, config: dict):
        self.grid = grid
        self.config = config
        self.console = Console()
        self._tick: int = 0
        self._alive: int = 0
        self._energy: float = 0.0
        self._events: list[str] = []

        bus.subscribe(EventType.TICK_END, self._on_tick_end)
        bus.subscribe(EventType.CELL_CREATED, self._on_cell_created)
        bus.subscribe(EventType.CELL_DESTROYED, self._on_cell_destroyed)

    def _on_tick_end(self, event) -> None:
        self._tick = event.data["tick"]
        self._alive = event.data["alive_count"]
        self._energy = event.data["total_energy"]

    def _on_cell_created(self, event) -> None:
        self._events.append(
            f"[green]+[/] {event.data['cell_id'][:8]} "
            f"t={event.data['type']} @({event.data['x']},{event.data['y']})"
        )
        if len(self._events) > 8:
            self._events = self._events[-8:]

    def _on_cell_destroyed(self, event) -> None:
        self._events.append(
            f"[red]-[/] {event.data['cell_id'][:8]} "
            f"({event.data['reason']})"
        )
        if len(self._events) > 8:
            self._events = self._events[-8:]

    def build_layout(self) -> Layout:
        w = self.config["world"]
        layout = Layout()
        layout.split_column(
            Layout(Panel("DAO Genesis — Phase 0", border_style="bold cyan"), name="header", size=2),
            Layout(name="body"),
            Layout(name="footer", size=8),
        )

        grid_str = make_grid_display(self.grid, w["width"], w["height"])
        layout["body"].update(Panel(grid_str, title="Universe", border_style="green"))

        stats = (
            f"Tick: {self._tick:>6}  |  "
            f"Alive: {self._alive:>4}  |  "
            f"Energy: {self._energy:>8.1f}"
        )
        events = "\n".join(self._events[-6:]) if self._events else "No events yet"
        footer = Panel(f"{stats}\n{'-' * 60}\n{events}",
                       title="Stats", border_style="yellow")
        layout["footer"].update(footer)
        return layout

    def display_tick(self, live: Live) -> None:
        live.update(self.build_layout())
