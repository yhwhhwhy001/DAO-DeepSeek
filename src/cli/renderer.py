"""CLI Renderer — Rich-based Phase 1 terminal display."""
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
    def __init__(self, grid: Grid, bus: EventBus, config: dict,
                 detector=None, entropy_engine=None, leaderboard_fn=None, pattern_hasher=None):
        self.grid = grid
        self.config = config
        self.console = Console()
        self.detector = detector
        self.entropy = entropy_engine
        self.leaderboard_fn = leaderboard_fn
        self.pattern_hasher = pattern_hasher

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
        self._events.append(f"[green]+[/] {event.data['cell_id'][:8]} "
                            f"t={event.data['type']} @({event.data['x']},{event.data['y']})")
        if len(self._events) > 8:
            self._events = self._events[-8:]

    def _on_cell_destroyed(self, event) -> None:
        self._events.append(f"[red]-[/] {event.data['cell_id'][:8]} "
                            f"({event.data['reason']})")
        if len(self._events) > 8:
            self._events = self._events[-8:]

    def build_layout(self) -> Layout:
        w = self.config["world"]
        layout = Layout()

        # Header
        header_text = f"DAO Genesis — Phase 1   Tick: {self._tick}"
        layout.split_column(
            Layout(Panel(header_text, border_style="bold cyan"), name="header", size=2),
            Layout(name="main"),
            Layout(name="footer", size=3),
        )

        # Main: left (grid) + right (panels)
        layout["main"].split_row(
            Layout(name="left", ratio=3),
            Layout(name="right", ratio=2),
        )

        # Left: universe grid
        grid_str = make_grid_display(self.grid, w["width"], w["height"])
        layout["left"].update(Panel(grid_str, title="Universe", border_style="green"))

        # Right: stacked panels (Entropy, Leaderboard, Events)
        right_panels = []

        # Entropy panel
        if self.entropy and self.entropy.current_snapshot:
            snap = self.entropy.current_snapshot
            trend = self.entropy.current_trend
            trend_styles = {"ordering": "green", "chaos": "red", "steady": "yellow", "diversifying": "blue"}
            style = trend_styles.get(trend, "white")
            entropy_text = (
                f"Global:  {snap['global_entropy']:.2f} bits\n"
                f"Local:   {snap['local_entropy_mean']:.2f} ± {snap['local_entropy_std']:.2f}\n"
                f"Struct:  {snap['structure_entropy']:.2f} bits\n"
                f"Trend:   [{style}]{trend}[/{style}]"
            )
            right_panels.append(Panel(entropy_text, title="Entropy", border_style="blue"))

        # Leaderboard panel
        if self.detector and self.leaderboard_fn:
            structs = self.detector.get_active()
            stable = self.detector.get_stable()
            pattern_occs = {}
            if self.pattern_hasher:
                pattern_occs = {h: r.total_occurrences for h, r in self.pattern_hasher.patterns.items()}

            struct_dicts = []
            for s in structs:
                type_count = 1
                if s.cells:
                    types_seen = set()
                    for c in self.grid.all_cells:
                        if c.id in s.cells:
                            types_seen.add(c.type)
                    type_count = len(types_seen)
                struct_dicts.append({
                    "id": s.id,
                    "age": s.age,
                    "size": len(s.cells),
                    "type_count": type_count,
                    "shape_hash": s.shape_hash,
                })

            ranked = self.leaderboard_fn(struct_dicts, pattern_occs, top_n=5)
            n_patterns = self.pattern_hasher.unique_count() if self.pattern_hasher else 0
            lb_lines = [f"Total: {len(structs)} ({len(stable)} stable) | Patterns: {n_patterns}"]
            for i, r in enumerate(ranked, 1):
                lb_lines.append(
                    f"{i}. {r['id']}  age={r['age']}  sz={r['size']}  "
                    f"hash={r.get('shape_hash','')[:6]}  score={r['score']:.2f}"
                )
            right_panels.append(Panel("\n".join(lb_lines), title="Leaderboard", border_style="magenta"))

        # Event log
        events = "\n".join(self._events[-6:]) if self._events else "No events yet"
        right_panels.append(Panel(events, title="Events", border_style="yellow"))

        # Layout right column
        right_layout = Layout()
        if len(right_panels) == 1:
            right_layout.update(right_panels[0])
        elif len(right_panels) == 2:
            right_layout.split_column(
                Layout(right_panels[0], name="r0"),
                Layout(right_panels[1], name="r1"),
            )
        else:
            right_layout.split_column(
                Layout(right_panels[0], name="r0", ratio=2),
                Layout(right_panels[1], name="r1", ratio=3),
                Layout(right_panels[2], name="r2", ratio=2),
            )
        layout["right"].update(right_layout)

        # Footer
        active = self.detector.active_count if self.detector else 0
        stable_c = self.detector.stable_count if self.detector else 0
        footer_text = (f"Alive: {self._alive}  |  Energy: {self._energy:.1f}  |  "
                       f"Structures: {active} ({stable_c} stable)")
        layout["footer"].update(Panel(footer_text, border_style="dim cyan"))

        return layout

    def display_tick(self, live: Live) -> None:
        live.update(self.build_layout())
