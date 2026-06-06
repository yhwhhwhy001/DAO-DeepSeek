"""CLI 渲染器 — 基于 Rich 的第一阶段终端显示。"""
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
                 cognition_data: dict | None = None,
                 civilization_data: dict | None = None):
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
        self._civ = civilization_data

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

        # 头部
        header_text = f"DAO 创世纪 — 阶段一   Tick: {self._tick}"
        layout.split_column(
            Layout(Panel(header_text, border_style="bold cyan"), name="header", size=2),
            Layout(name="main"),
            Layout(name="footer", size=3),
        )

        # 主区域：左侧（网格）+ 右侧（面板）
        layout["main"].split_row(
            Layout(name="left", ratio=3),
            Layout(name="right", ratio=2),
        )

        # 左侧：宇宙网格
        remnants_dict = {}
        if self._ecology:
            remnants_dict = self._ecology.get("remnants", {})
        grid_str = make_grid_display(self.grid, w["width"], w["height"], remnants_dict)
        layout["left"].update(Panel(grid_str, title="宇宙", border_style="green"))

        # 右侧：堆叠面板
        right_panels = []

        # 熵面板
        if self.entropy and self.entropy.current_snapshot:
            snap = self.entropy.current_snapshot
            trend = self.entropy.current_trend
            trend_styles = {"ordering": "green", "chaos": "red", "steady": "yellow", "diversifying": "blue"}
            style = trend_styles.get(trend, "white")
            trend_labels = {"ordering": "有序化", "chaos": "混沌化", "steady": "稳态", "diversifying": "多样化"}
            trend_label = trend_labels.get(trend, trend)
            entropy_text = (
                f"全局熵:  {snap['global_entropy']:.2f} bit\n"
                f"局部熵:   {snap['local_entropy_mean']:.2f} ± {snap['local_entropy_std']:.2f}\n"
                f"结构熵:  {snap['structure_entropy']:.2f} bit\n"
                f"趋势:   [{style}]{trend_label}[/{style}]"
            )
            right_panels.append(Panel(entropy_text, title="熵", border_style="blue"))

        # 排行榜面板
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
            lb_lines = [f"总计: {len(structs)} ({len(stable)} 稳定) | 模式: {n_patterns}"]
            for i, r in enumerate(ranked, 1):
                lb_lines.append(
                    f"{i}. {r['id']}  age={r['age']}  sz={r['size']}  "
                    f"hash={r.get('shape_hash','')[:6]}  得分={r['score']:.2f}"
                )
            right_panels.append(Panel("\n".join(lb_lines), title="排行榜", border_style="magenta"))

        # 决策面板
        if self._decision:
            ds = self._decision
            dec_text = (
                f"Q表细胞: {ds.get('q_cells', 0)}  |  "
                f"活跃: {ds.get('non_stay_pct', 0):.0f}%\n"
                f"首选动作: {ds.get('top_action', 'N/A')}"
            )
            if ds.get('top_rules'):
                dec_text += f"\n首选规则: {ds['top_rules'][0] if ds['top_rules'] else 'N/A'}"
            right_panels.append(Panel(dec_text, title="决策", border_style="green"))

        # 生命面板
        if self._life:
            ls = self._life
            proto = ls.get("proto_count", 0)
            true_count = ls.get("true_count", 0)
            life_text = f"准生命: {proto}  |  真生命: {true_count}"
            top = ls.get("top_lifeforms", [])
            for i, lf in enumerate(top[:3], 1):
                life_text += f"\n{i}. {lf['id']}  score={lf['score']:.1f}  {lf['class']}"
            right_panels.append(Panel(life_text, title="生命", border_style="bright_green"))

        # 生态面板
        if self._ecology:
            ed = self._ecology
            eco_text = f"节点: {ed.get('nodes', 0)}  |  边: {ed.get('edges', 0)}"
            competitors = ed.get("competition_pairs", 0)
            mutualists = ed.get("mutualism_pairs", 0)
            eco_text += f"\n竞争: {competitors}  |  互惠: {mutualists}"
            eco_text += f"\n残骸: {ed.get('remnant_count', 0)}"
            right_panels.append(Panel(eco_text, title="生态", border_style="yellow"))

        # 认知面板
        if self._cog:
            cg = self._cog
            cog_text = f"符号: {cg.get('symbols', 0)}  |  知识: {cg.get('knowledge', 0)}"
            cog_text += f"\n信号: {cg.get('signals', 0)}  |  跨谱系: {cg.get('cross_lineage_pct', 0):.0f}%"
            cog_text += f"\n首选符号: {cg.get('top_symbol', 'N/A')}"
            right_panels.append(Panel(cog_text, title="认知", border_style="bright_cyan"))

        # 文明面板
        if self._civ:
            cv = self._civ
            civ_text = f"活跃: {cv.get('active_civs', 0)}  |  灭亡: {cv.get('fallen_civs', 0)}"
            top = cv.get('top_civ')
            if top:
                civ_text += f"\n首位: {top.get('id', 'N/A')} 时代={top.get('era', '?')} 规模={top.get('size', 0)}"
                hero = cv.get('hero_narrative', '')
                if hero:
                    civ_text += f"\n英雄: {hero[:60]}..."
            right_panels.append(Panel(civ_text, title="文明", border_style="bright_magenta"))

        # 谱系面板
        if self._lineage and self._lineage.get("max_depth", 0) > 0:
            ld = self._lineage
            trend = ld.get("lifespan_trend", "?")
            trend_labels = {"increasing": "增长", "decreasing": "下降", "stable": "稳定", "insufficient_data": "数据不足"}
            trend_label = trend_labels.get(trend, trend)
            lineage_text = (
                f"世代: {len(ld.get('generations', {}))}  |  "
                f"谱系: {ld.get('total_lineages', 0)}  |  "
                f"最大深度: {ld.get('max_depth', 0)}\n"
                f"寿命趋势: {trend_label}"
            )
            shapes = ld.get("shape_inheritance", {})
            if shapes:
                top_shapes = sorted(shapes.items(), key=lambda kv: kv[1]["generations"], reverse=True)[:3]
                lineage_text += "\n形态传承:"
                for h, info in top_shapes:
                    lineage_text += f"\n  {h[:8]}: {info['generations']} 代"
            right_panels.append(Panel(lineage_text.strip(), title="谱系", border_style="cyan"))

        # 事件日志
        events = "\n".join(self._events[-6:]) if self._events else "暂无事件"
        right_panels.append(Panel(events, title="事件", border_style="yellow"))

        # 布局右侧列
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
        elif len(right_panels) == 9:
            right_layout.split_column(
                Layout(right_panels[0], name="r0", ratio=2),
                Layout(right_panels[1], name="r1", ratio=3),
                Layout(right_panels[2], name="r2", ratio=1),
                Layout(right_panels[3], name="r3", ratio=2),
                Layout(right_panels[4], name="r4", ratio=2),
                Layout(right_panels[5], name="r5", ratio=2),
                Layout(right_panels[6], name="r6", ratio=1),
                Layout(right_panels[7], name="r7", ratio=1),
                Layout(right_panels[8], name="r8", ratio=1),
            )
        else:
            right_layout.split_column(
                Layout(right_panels[0], name="r0", ratio=2),
                Layout(right_panels[1], name="r1", ratio=3),
                Layout(right_panels[2], name="r2", ratio=2),
                Layout(right_panels[3], name="r3", ratio=2),
            )
        layout["right"].update(right_layout)

        # 底部
        active = self.detector.active_count if self.detector else 0
        stable_c = self.detector.stable_count if self.detector else 0
        footer_text = (f"存活: {self._alive}  |  能量: {self._energy:.1f}  |  "
                       f"结构: {active} ({stable_c} 稳定)")
        layout["footer"].update(Panel(footer_text, border_style="dim cyan"))

        return layout

    def display_tick(self, live: Live) -> None:
        live.update(self.build_layout())
