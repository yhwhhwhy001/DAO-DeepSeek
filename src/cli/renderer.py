"""CLI Renderer — Rich-based Phase 1 terminal display."""
from rich.live import Live
from rich.panel import Panel
from rich.layout import Layout
from rich.console import Console
from src.grid import Grid
from src.event_bus import EventBus, EventType

TYPE_CHARS = {0: "·", 1: "○", 2: "◇", 3: "□"}


def make_grid_display(grid: Grid, width: int, height: int, remnants=None) -> str:
    lines = []
    for y in range(height):
        row = []
        for x in range(width):
            cell = grid.get(x, y)
            if cell:
                row.append(TYPE_CHARS.get(cell.type, "?"))
            elif remnants and (x, y) in remnants:
                row.append("+")
            else:
                row.append(" ")
        lines.append("".join(row))
    return "\n".join(lines)


class Renderer:
    def __init__(self, grid: Grid, bus: EventBus, config: dict,
                 detector=None, entropy_engine=None, leaderboard_fn=None,
                 pattern_hasher=None, lineage_data: dict | None = None,
                 decision_stats: dict | None = None,
                 life_stats: dict | None = None,
                 ecology_data: dict | None = None,
                 cognition_data: dict | None = None):
        self.grid = grid
        self.config = config
        self.console = Console()
        self.detector = detector
        self.entropy = entropy_engine
        self.leaderboard_fn = leaderboard_fn
        self.pattern_hasher = pattern_hasher
        self._lineage = lineage_data
        self._decision = decision_stats
        self._life = life_stats
        self._ecology = ecology_data
        self._cog = cognition_data

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
        remnants_dict = {}
        if self._ecology:
            remnants_dict = self._ecology.get("remnants", {})
        grid_str = make_grid_display(self.grid, w["width"], w["height"], remnants_dict)
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

        # Decision panel
        if self._decision:
            ds = self._decision
            dec_text = (
                f"Q-cells: {ds.get('q_cells', 0)}  |  "
                f"Active: {ds.get('non_stay_pct', 0):.0f}%\n"
                f"Top action: {ds.get('top_action', 'N/A')}"
            )
            if ds.get('top_rules'):
                dec_text += f"\nTop rule: {ds['top_rules'][0] if ds['top_rules'] else 'N/A'}"
            right_panels.append(Panel(dec_text, title="Decision", border_style="green"))

        # Life panel
        if self._life:
            ls = self._life
            proto = ls.get("proto_count", 0)
            true_count = ls.get("true_count", 0)
            life_text = f"Proto-lifeforms: {proto}  |  True lifeforms: {true_count}"
            top = ls.get("top_lifeforms", [])
            for i, lf in enumerate(top[:3], 1):
                life_text += f"\n{i}. {lf['id']}  score={lf['score']:.1f}  {lf['class']}"
            right_panels.append(Panel(life_text, title="Life", border_style="bright_green"))

        # Ecology panel
        if self._ecology:
            ed = self._ecology
            eco_text = f"Nodes: {ed.get('nodes', 0)}  |  Edges: {ed.get('edges', 0)}"
            competitors = ed.get("competition_pairs", 0)
            mutualists = ed.get("mutualism_pairs", 0)
            eco_text += f"\nCompetition: {competitors}  |  Mutualism: {mutualists}"
            eco_text += f"\nRemnants: {ed.get('remnant_count', 0)}"
            right_panels.append(Panel(eco_text, title="Ecology", border_style="yellow"))

        # Cognition panel
        if self._cog:
            cg = self._cog
            cog_text = f"Symbols: {cg.get('symbols', 0)}  |  Knowledge: {cg.get('knowledge', 0)}"
            cog_text += f"\nSignals: {cg.get('signals', 0)}  |  Cross-lin: {cg.get('cross_lineage_pct', 0):.0f}%"
            cog_text += f"\nTop symbol: {cg.get('top_symbol', 'N/A')}"
            right_panels.append(Panel(cog_text, title="Cognition", border_style="bright_cyan"))

        # Lineage panel
        if self._lineage and self._lineage.get("max_depth", 0) > 0:
            ld = self._lineage
            trend = ld.get("lifespan_trend", "?")
            lineage_text = (
                f"Generations: {len(ld.get('generations', {}))}  |  "
                f"Lineages: {ld.get('total_lineages', 0)}  |  "
                f"Max Depth: {ld.get('max_depth', 0)}\n"
                f"Lifespan Trend: {trend}"
            )
            shapes = ld.get("shape_inheritance", {})
            if shapes:
                top_shapes = sorted(shapes.items(), key=lambda kv: kv[1]["generations"], reverse=True)[:3]
                lineage_text += "\nTop Shapes:"
                for h, info in top_shapes:
                    lineage_text += f"\n  {h[:8]}: {info['generations']} gens"
            right_panels.append(Panel(lineage_text.strip(), title="Lineage", border_style="cyan"))

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
        elif len(right_panels) == 3:
            right_layout.split_column(
                Layout(right_panels[0], name="r0", ratio=2),
                Layout(right_panels[1], name="r1", ratio=3),
                Layout(right_panels[2], name="r2", ratio=2),
            )
        elif len(right_panels) == 4:
            right_layout.split_column(
                Layout(right_panels[0], name="r0", ratio=2),
                Layout(right_panels[1], name="r1", ratio=3),
                Layout(right_panels[2], name="r2", ratio=2),
                Layout(right_panels[3], name="r3", ratio=2),
            )
        elif len(right_panels) == 5:
            right_layout.split_column(
                Layout(right_panels[0], name="r0", ratio=2),
                Layout(right_panels[1], name="r1", ratio=3),
                Layout(right_panels[2], name="r2", ratio=1),
                Layout(right_panels[3], name="r3", ratio=2),
                Layout(right_panels[4], name="r4", ratio=2),
            )
        elif len(right_panels) == 6:
            right_layout.split_column(
                Layout(right_panels[0], name="r0", ratio=2),
                Layout(right_panels[1], name="r1", ratio=3),
                Layout(right_panels[2], name="r2", ratio=1),
                Layout(right_panels[3], name="r3", ratio=2),
                Layout(right_panels[4], name="r4", ratio=2),
                Layout(right_panels[5], name="r5", ratio=2),
            )
        elif len(right_panels) == 7:
            right_layout.split_column(
                Layout(right_panels[0], name="r0", ratio=2),
                Layout(right_panels[1], name="r1", ratio=3),
                Layout(right_panels[2], name="r2", ratio=1),
                Layout(right_panels[3], name="r3", ratio=2),
                Layout(right_panels[4], name="r4", ratio=2),
                Layout(right_panels[5], name="r5", ratio=2),
                Layout(right_panels[6], name="r6", ratio=1),
            )
        elif len(right_panels) == 8:
            right_layout.split_column(
                Layout(right_panels[0], name="r0", ratio=2),
                Layout(right_panels[1], name="r1", ratio=3),
                Layout(right_panels[2], name="r2", ratio=1),
                Layout(right_panels[3], name="r3", ratio=2),
                Layout(right_panels[4], name="r4", ratio=2),
                Layout(right_panels[5], name="r5", ratio=2),
                Layout(right_panels[6], name="r6", ratio=1),
                Layout(right_panels[7], name="r7", ratio=1),
            )
        else:
            right_layout.split_column(
                Layout(right_panels[0], name="r0", ratio=2),
                Layout(right_panels[1], name="r1", ratio=3),
                Layout(right_panels[2], name="r2", ratio=2),
                Layout(right_panels[3], name="r3", ratio=2),
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
