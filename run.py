"""DAO Genesis — Phase 3 Decision Emergence."""
import sys
import time
import yaml
import random
from rich.live import Live
from src.world_engine import WorldEngine
from src.event_bus import EventType
from src.structure_detector import StructureDetector
from src.pattern_hasher import PatternHasher
from src.entropy_engine import EntropyEngine
from src.leaderboard import build_leaderboard
from src.memory_engine import MemoryEngine
from src.lineage_analyzer import LineageAnalyzer
from src.death_predictor import DeathPredictor, extract_features
from src.decision_engine import DecisionEngine
from src.ruleset import generate_random_ruleset
from src.life_detector import LifeDetector
from src.rule_evolution import RuleEvolutionTracker
from src.cli.renderer import Renderer


def main():
    config_path = "experiments/phase1_optimized.yaml"
    if len(sys.argv) > 1:
        config_path = sys.argv[1]

    with open(config_path) as f:
        config = yaml.safe_load(f)

    print(f"DAO Genesis Phase 3 — {config['experiment']['name']}")
    print("Press Ctrl+C to stop.\n")

    world = WorldEngine(config)

    # Phase 1
    detector = StructureDetector(world.grid, world.bus)
    pattern_hasher = PatternHasher()
    entropy = EntropyEngine(world.grid, world.bus, detector,
                            num_types=config["physics"]["num_types"])

    # Phase 2
    memory_engine = MemoryEngine(world.bus, detector)
    lineage_analyzer = LineageAnalyzer()
    death_predictor = DeathPredictor()
    lineage_data: dict = {}

    # Phase 3
    rng = random.Random(42)
    decision_engine = DecisionEngine(world.grid, seed=42)
    decision_engine._detector = detector
    tracker = RuleEvolutionTracker()
    life_detector = LifeDetector(world.bus)
    life_stats = {"proto_count": 0, "true_count": 0, "top_lifeforms": []}

    # Register initial cells
    for cell in list(world.grid.all_cells):
        rs = generate_random_ruleset(rng)
        decision_engine.register_cell(cell.id, rs)

    # Wire decision engine to time engine
    world.time_engine.decision_engine = decision_engine

    # Subscribe to fission for inheritance
    def on_fission(event):
        decision_engine.inherit_on_fission(
            event.data["parent_id"], event.data["child_id"], rng)

    world.bus.subscribe(EventType.STRUCTURE_FISSION, on_fission)

    # Remove dead cells from decision engine
    def on_cell_destroyed(event):
        decision_engine.remove_cell(event.data["cell_id"])

    world.bus.subscribe(EventType.CELL_DESTROYED, on_cell_destroyed)

    def on_structure_lost(event):
        life_detector.on_structure_lost(
            event.data["structure_id"], world.time_engine.tick)
    world.bus.subscribe(EventType.STRUCTURE_LOST, on_structure_lost)

    decision_stats = {"q_cells": 0, "non_stay_pct": 0,
                      "top_action": "N/A", "top_rules": []}

    def on_tick_end_all(event):
        tick = event.data["tick"]

        for s in detector.get_active():
            if s.shape_hash:
                pattern_hasher.register(s.shape_hash, tick, (0, 0))

        # Decision stats every 20 ticks
        if tick % 20 == 0:
            action_counts = {}
            for dc in decision_engine.cells.values():
                action_counts[dc.last_action] = \
                    action_counts.get(dc.last_action, 0) + 1
            total = sum(action_counts.values())
            non_stay = sum(v for k, v in action_counts.items()
                           if k != "STAY")
            q_cells = sum(1 for dc in decision_engine.cells.values()
                          if len(dc.utility._q_table) > 0)
            top_action = max(action_counts, key=action_counts.get) \
                if action_counts else "N/A"

            # Track rules
            for cell in world.grid.all_cells:
                if cell.id in decision_engine.cells:
                    dc = decision_engine.cells[cell.id]
                    tracker.record_ruleset(cell.id, dc.ruleset,
                                           survived=cell.energy > 0)

            decision_stats.update({
                "q_cells": q_cells,
                "non_stay_pct": non_stay / max(total, 1) * 100,
                "top_action": top_action,
                "top_rules": [r["signature"]
                              for r in tracker.get_top_rules(3)],
            })

        # Life detection every 10 ticks
        if tick % 10 == 0:
            proto_count = 0
            true_count = 0
            for s in detector.get_active():
                if s.age < 10:
                    continue
                mem = memory_engine.memories.get(s.id)
                mem_data = {
                    "snapshot_count": len(mem.snapshots) if mem else 0,
                    "event_types": len(set(e.event_type for e in mem.events)) if mem else 0,
                    "has_parent": bool(mem.parent_id) if mem else False,
                    "has_children": len(mem.fission_children) > 0 if mem else False,
                    "fission_children": mem.fission_children if mem else [],
                    "max_lineage_generation": 0,
                }
                dec_data = {"total_actions": 1, "non_stay": 0, "q_entries": 0, "unique_actions": 1}
                if decision_engine:
                    cell_ids = list(s.cells)
                    if cell_ids and cell_ids[0] in decision_engine.cells:
                        dc = decision_engine.cells[cell_ids[0]]
                        actions = [dc.last_action]
                        dec_data = {
                            "total_actions": max(dc.age, 1),
                            "non_stay": 0 if dc.last_action == "STAY" else dc.age,
                            "q_entries": len(dc.utility._q_table),
                            "unique_actions": len(set(actions)),
                        }
                adapt_data = {
                    "snapshots": [{"total_energy": snap.total_energy} for snap in (mem.snapshots if mem else [])],
                    "events": [{"event_type": e.event_type} for e in (mem.events if mem else [])],
                }
                result = life_detector.evaluate(
                    s.id, tick, age=s.age, is_stable=s.status=="stable",
                    generation=mem.generation if mem else 0,
                    memory_data=mem_data, decision_data=dec_data, adaptation_data=adapt_data,
                )
                if result["classification"] == "proto-lifeform":
                    proto_count += 1
                elif result["classification"] == "true-lifeform":
                    true_count += 1

            lifeforms = life_detector.get_lifeforms()
            top = []
            for lf in sorted(lifeforms, key=lambda r: r.peak_score, reverse=True)[:5]:
                latest = lf.assessments[-1] if lf.assessments else None
                top.append({
                    "id": lf.structure_id,
                    "score": lf.peak_score,
                    "class": latest.classification if latest else "unknown",
                })
            life_stats.update({
                "proto_count": proto_count,
                "true_count": true_count,
                "top_lifeforms": top,
            })

    world.bus.subscribe(EventType.TICK_END, on_tick_end_all)

    renderer = Renderer(
        world.grid, world.bus, config,
        detector=detector,
        entropy_engine=entropy,
        leaderboard_fn=build_leaderboard,
        pattern_hasher=pattern_hasher,
        lineage_data=lineage_data,
        decision_stats=decision_stats,
        life_stats=life_stats,
    )

    fps = 15
    try:
        with Live(renderer.build_layout(), console=renderer.console,
                  refresh_per_second=fps, screen=True) as live:
            while True:
                world.time_engine.step()
                renderer._lineage = lineage_data
                renderer._decision = decision_stats
                renderer._life = life_stats
                renderer.display_tick(live)
                time.sleep(1.0 / fps)
    except KeyboardInterrupt:
        pass

    print(f"\nUniverse stopped at tick {world.time_engine.tick}")
    print(f"Cells: {world.grid.alive_count}")
    print(f"Decision cells: {len(decision_engine.cells)}")
    stats = tracker.get_stats()
    print(f"Rules tracked: {stats['total_rules']}")
    print(f"Top rules: {tracker.get_top_rules(5)}")


if __name__ == "__main__":
    main()
