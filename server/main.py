"""DAO Genesis Web 服务端 — FastAPI + WebSocket"""
import asyncio
import yaml
import random
from pathlib import Path
from fastapi import FastAPI, WebSocket
from fastapi.staticfiles import StaticFiles
from src.world_engine import WorldEngine
from src.event_bus import EventType
from src.structure_detector import StructureDetector
from src.pattern_hasher import PatternHasher
from src.entropy_engine import EntropyEngine
from src.leaderboard import build_leaderboard
from src.memory_engine import MemoryEngine
from src.lineage_analyzer import LineageAnalyzer
from src.decision_engine import DecisionEngine
from src.ruleset import generate_random_ruleset
from src.life_detector import LifeDetector
from src.map_engine import MapEngine
from src.resource_engine import ResourceEngine
from src.ecology_engine import EcologyEngine
from src.symbol_engine import SymbolEngine
from src.knowledge_engine import KnowledgeEngine
from src.language_engine import LanguageEngine
from src.civilization_engine import CivilizationEngine
from src.cultivator import Cultivator, SPELL_COSTS
from src.beast_engine import BeastEngine
from src.history_engine import HistoryEngine
from src.myth_engine import MythEngine

app = FastAPI(title="DAO Genesis")


class GameSession:
    def __init__(self):
        self.world: WorldEngine | None = None
        self.running = False
        self.tps = 60
        self._tick = 0
        self.player = None
        # Lazy-init attributes
        self.detector = None
        self.pattern_hasher = None
        self.entropy = None
        self.memory = None
        self.lineage_analyzer = None
        self.decision = None
        self.life = None
        self.map_engine = None
        self.resource = None
        self.ecology = None
        self.symbol_engine = None
        self.knowledge_engine = None
        self.language_engine = None
        self.civ_engine = None
        self.history = None
        self.myth = None

    def init(self, config_path: str):
        with open(config_path) as f:
            config = yaml.safe_load(f)

        self.world = WorldEngine(config)

        self.detector = StructureDetector(self.world.grid, self.world.bus)
        self.pattern_hasher = PatternHasher()
        self.entropy = EntropyEngine(self.world.grid, self.world.bus, self.detector,
                                     num_types=config["physics"]["num_types"])
        self.memory = MemoryEngine(self.world.bus, self.detector)
        self.lineage_analyzer = LineageAnalyzer()

        rng = random.Random(42)
        self.decision = DecisionEngine(self.world.grid, seed=42)
        self.decision._detector = self.detector
        for cell in list(self.world.grid.all_cells):
            self.decision.register_cell(cell.id, generate_random_ruleset(rng))
        self.world.time_engine.decision_engine = self.decision

        self.life = LifeDetector(self.world.bus)
        self.map_engine = MapEngine(height=config["world"]["height"])
        self.resource = ResourceEngine()
        self.ecology = EcologyEngine()
        self.symbol_engine = SymbolEngine()
        self.knowledge_engine = KnowledgeEngine()
        self.language_engine = LanguageEngine()
        self.civ_engine = CivilizationEngine(self.world.bus)
        self.history = HistoryEngine()
        self.myth = MythEngine()

        self.world.state_engine.map_engine = self.map_engine
        self.world.state_engine.resource_engine = self.resource
        self.world.time_engine.resource_engine = self.resource
        self.beast_engine = BeastEngine(self.world.grid, seed=42)

        from src.cell import Cell
        pos = self.world.grid.random_empty_position()
        if pos:
            player_cell = Cell(x=pos[0], y=pos[1], type=0, energy=20.0)
            self.world.grid.place(player_cell)
            self.decision.register_cell(player_cell.id, generate_random_ruleset(rng))
            self.player = Cultivator(player_cell.id)
            self.player._rng = rng

        def on_fission(event):
            self.decision.inherit_on_fission(event.data["parent_id"], event.data["child_id"], rng)
        self.world.bus.subscribe(EventType.STRUCTURE_FISSION, on_fission)

        def on_destroy(event):
            self.decision.remove_cell(event.data["cell_id"])
        self.world.bus.subscribe(EventType.CELL_DESTROYED, on_destroy)

    def step(self) -> dict:
        # 玩家 tick
        player_data = None
        if self.player and self.player.cell_id:
            player_cell = self.world.grid.get_by_id(self.player.cell_id)
            if player_cell:
                self.player.energy = player_cell.energy
                self.player.max_energy = max(self.player.max_energy, player_cell.energy)
                self.player.tick_age += 1
                if self.player.shield_ticks > 0:
                    self.player.shield_ticks -= 1
                self.player.try_breakthrough()
                player_data = {
                    "energy": round(self.player.energy, 1),
                    "max_energy": round(self.player.max_energy, 1),
                    "realm": self.player.realm.name,
                    "realm_index": self.player._realm_index,
                    "skills": self.player.skills,
                    "discovered_skills": self.player.discovered_skills,
                    "herbs": self.player.herbs,
                    "shield_ticks": self.player.shield_ticks,
                    "reincarnation": self.player.reincarnation_count,
                    "cell_id": self.player.cell_id,
                }
            else:
                self.player = None

        # 妖兽阶段
        px = None; py = None; pc = None
        if self.player:
            pc = self.world.grid.get_by_id(self.player.cell_id)
            if pc:
                px, py = pc.x, pc.y
        beast_events = self.beast_engine.tick(px, py)
        for evt in beast_events:
            if evt["type"] == "beast_attack" and pc:
                dmg = evt["damage"]
                if self.player.shield_ticks > 0:
                    dmg *= 0.5
                buffs = self.player.get_skill_buffs()
                dmg *= (1 - buffs["damage_reduce"])
                pc.energy -= dmg
                if pc.energy > dmg * 3:
                    if self.beast_engine.damage_beast(evt["id"], pc.energy * 0.1):
                        self.player.total_kills += 1
                        pc.energy += 5

        # 决策阶段 (跳过玩家细胞)
        if self.player:
            player_cell_id = self.player.cell_id
            self.decision.cells.pop(player_cell_id, None)
        self.decision.step_all(self.world.grid, self.world.bus)
        self.world.time_engine.step()
        # 恢复玩家到决策引擎
        if self.player and pc:
            pid = self.player.cell_id
            if pid not in self.decision.cells and pc.energy > 0:
                from src.ruleset import generate_random_ruleset
                self.decision.register_cell(pid, generate_random_ruleset(random.Random()))
        self._tick += 1

        g = self.world.grid
        # 压缩格式: [x, y, type, energy] 数组
        cells = [[c.x, c.y, c.type, round(c.energy, 1),
                  self.player.cell_id if self.player and c.id == self.player.cell_id else ""]
                 for c in g.all_cells]

        remnants = []
        if self.resource:
            remnants = [[r.x, r.y, r.type, round(r.energy, 1)] for r in self.resource.all_remnants]

        # 每 50 tick 更新符号和知识
        if self._tick % 50 == 0:
            q_data = []
            for dc in self.decision.cells.values():
                for sk, actions in dc.utility._q_table.items():
                    for a, v in actions.items():
                        if abs(v) > 0.1:
                            q_data.append((sk, a, v))
            symbols = self.symbol_engine.scan(q_data)
            transitions = []
            for dc in self.decision.cells.values():
                keys = set(dc.utility._q_table.keys())
                for s in symbols:
                    if s.state_keys & keys:
                        for s2 in symbols:
                            if s.id != s2.id and s2.state_keys & keys:
                                transitions.append((s.id, s2.id))
            new_knowledge = self.knowledge_engine.scan(transitions, {})
            # 功法发现
            if self.player and new_knowledge:
                from src.cultivator import discover_skill_from_knowledge
                for k in new_knowledge:
                    skill = discover_skill_from_knowledge(k.antecedent, k.consequent)
                    if skill and skill not in self.player.discovered_skills and len(self.player.discovered_skills) < 7:
                        self.player.discovered_skills.append(skill)

        entropy_data = None
        if self.entropy.current_snapshot:
            s = self.entropy.current_snapshot
            entropy_data = {
                "global": round(s["global_entropy"], 2),
                "local_mean": round(s["local_entropy_mean"], 2),
                "local_std": round(s["local_entropy_std"], 2),
                "structure": round(s["structure_entropy"], 2),
                "trend": self.entropy.current_trend,
            }

        active = self.detector.get_active()
        pattern_occs = {h: r.total_occurrences for h, r in self.pattern_hasher.patterns.items()}
        struct_dicts = []
        for s in active:
            types_seen = set()
            for c in g.all_cells:
                if c.id in s.cells:
                    types_seen.add(c.type)
            struct_dicts.append({"id": s.id, "age": s.age, "size": len(s.cells),
                                 "type_count": len(types_seen), "shape_hash": s.shape_hash})
        ranked = build_leaderboard(struct_dicts, pattern_occs, top_n=5)
        leaderboard_data = [{"id": r["id"], "age": r["age"], "size": r["size"],
                             "hash": r.get("shape_hash", "")[:6], "score": round(r["score"], 2)}
                            for r in ranked]

        lifeforms = self.life.get_lifeforms()
        life_data = {"proto": len([lf for lf in lifeforms if lf.peak_score >= 60]),
                     "true_count": len([lf for lf in lifeforms if lf.peak_score >= 80]),
                     "top": [{"id": lf.structure_id, "score": round(lf.peak_score, 1)}
                             for lf in sorted(lifeforms, key=lambda x: x.peak_score, reverse=True)[:3]]}

        lang_stats = self.language_engine.get_stats()
        cognition_data = {"symbols": len(self.symbol_engine.symbols),
                          "signals": lang_stats["total_signals"],
                          "top_symbol": lang_stats.get("top_symbol", "N/A")}

        return {
            "type": "tick",
            "tick": self._tick,
            "grid": {"width": g.width, "height": g.height,
                     "cells": cells, "remnants": remnants,
                     "beasts": self.beast_engine.get_all_data()},
            "stats": {"alive": g.alive_count, "energy": round(g.total_energy, 1),
                      "structures": self.detector.active_count,
                      "stable": self.detector.stable_count,
                      "lifeforms": len(lifeforms)},
            "player": player_data,
            "beasts": self.beast_engine.get_all_data(),
            "panels": {
                "entropy": entropy_data,
                "leaderboard": leaderboard_data,
                "life": life_data,
                "cognition": cognition_data,
            },
        }


session = GameSession()


@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    while True:
        msg = await ws.receive_json()
        cmd = msg.get("type")

        if cmd == "start":
            config = msg.get("config", "experiments/web.yaml")
            session.init(config)
            session.running = True
            asyncio.create_task(_run_loop(ws))

        elif cmd == "pause":
            session.running = False

        elif cmd == "resume":
            session.running = True

        elif cmd == "set_speed":
            session.tps = msg.get("tps", 60)

        elif cmd == "player_move":
            if session.player and session.world:
                dx, dy = msg.get("dx", 0), msg.get("dy", 0)
                cell = session.world.grid.get_by_id(session.player.cell_id)
                if cell:
                    nx, ny = cell.x + dx, cell.y + dy
                    resolved = session.world.grid._resolve(nx, ny)
                    if resolved and session.world.grid.is_empty(*resolved):
                        session.world.grid.remove(cell.x, cell.y)
                        cell.x, cell.y = resolved
                        session.world.grid.place(cell)

        elif cmd == "player_spell":
            if session.player:
                spell = msg.get("spell", "")
                if spell == "吐纳术":
                    cell = session.world.grid.get_by_id(session.player.cell_id)
                    if cell:
                        for dx in range(-2, 3):
                            for dy in range(-2, 3):
                                nx, ny = cell.x + dx, cell.y + dy
                                resolved = session.world.grid._resolve(nx, ny)
                                if resolved:
                                    absorbed = session.resource.absorb(*resolved, cell.type, 1.0)
                                    if absorbed > 0:
                                        cell.energy += absorbed * 3
                                        session.player.total_energy_absorbed += absorbed
                elif spell in SPELL_COSTS:
                    if session.player.cast(spell):
                        if spell == "血遁术":
                            cell = session.world.grid.get_by_id(session.player.cell_id)
                            if cell:
                                empty = session.world.grid.random_empty_position()
                                if empty:
                                    session.world.grid.remove(cell.x, cell.y)
                                    cell.x, cell.y = empty
                                    session.world.grid.place(cell)

        elif cmd == "player_equip_skill":
            if session.player:
                session.player.equip_skill(msg.get("skill", ""))

        elif cmd == "player_reincarnate":
            if session.player:
                pos = session.world.grid.random_empty_position()
                if pos:
                    from src.cell import Cell
                    new_cell = Cell(x=pos[0], y=pos[1], type=0,
                                    energy=session.player.energy * 0.3 + 5)
                    session.world.grid.place(new_cell)
                    session.decision.register_cell(new_cell.id,
                        generate_random_ruleset(random.Random(session.world._rng.randint(0, 10000))))
                    session.player = session.player.reincarnate(new_cell.id)


async def _run_loop(ws: WebSocket):
    while True:
        try:
            if session.running and session.world:
                if session.tps == 0:
                    # 极速模式: 批量 50 tick，只发最后一次状态
                    state = None
                    for _ in range(50):
                        state = session.step()
                    if state:
                        state["grid"] = {}  # 不发送网格数据
                        await ws.send_json(state)
                elif session.tps >= 1000:
                    # 高速模式: 每 3 tick 发一次完整数据，其余只发统计
                    state = session.step()
                    if session._tick % 3 == 0:
                        await ws.send_json(state)
                    else:
                        await ws.send_json({
                            "type": "tick",
                            "tick": session._tick,
                            "grid": {},  # 空网格，前端复用上次数据
                            "stats": state["stats"],
                            "panels": state["panels"],
                        })
                else:
                    state = session.step()
                    await ws.send_json(state)
                    await asyncio.sleep(1 / session.tps)
            else:
                await asyncio.sleep(0.1)
        except Exception:
            break


static_dir = Path(__file__).parent.parent / "client" / "dist"
if static_dir.exists():
    app.mount("/", StaticFiles(directory=str(static_dir), html=True))
