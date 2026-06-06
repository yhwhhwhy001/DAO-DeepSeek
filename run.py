"""DAO Genesis — Phase 2 Memory Emergence."""
import sys
import time
import yaml
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
from src.cli.renderer import Renderer

LINEAGE_REPORT_INTERVAL = 100
RETRAIN_INTERVAL = 20


def main():
    config_path = "experiments/phase1_optimized.yaml"
    if len(sys.argv) > 1:
        config_path = sys.argv[1]

    with open(config_path) as f:
        config = yaml.safe_load(f)

    print(f"DAO Genesis Phase 2 — {config['experiment']['name']}")
    print(f"World: {config['world']['width']}x{config['world']['height']}, "
          f"boundary={config['world']['boundary']}, seed={config['world']['seed']}")
    print("Press Ctrl+C to stop.\n")

    world = WorldEngine(config)

    detector = StructureDetector(world.grid, world.bus)
    pattern_hasher = PatternHasher()
    num_types = config["physics"]["num_types"]
    entropy = EntropyEngine(world.grid, world.bus, detector, num_types=num_types)

    memory_engine = MemoryEngine(world.bus, detector)
    lineage_analyzer = LineageAnalyzer()
    death_predictor = DeathPredictor()
    lineage_data: dict = {}

    def on_tick_end_all(event):
        tick = event.data["tick"]

        for s in detector.get_active():
            if s.shape_hash:
                pattern_hasher.register(s.shape_hash, tick, (0, 0))

        if tick % LINEAGE_REPORT_INTERVAL == 0 and tick > 0:
            active_mems = list(memory_engine.memories.values())
            dead_mems = memory_engine.dead_memories
            ld = lineage_analyzer.analyze(active_mems, dead_mems)
            lineage_data.clear()
            lineage_data.update(ld)
            print(f"\n=== Lineage Report (tick {tick}) ===")
            print(f"Generations: {len(ld.get('generations', {}))} | "
                  f"Lineages: {ld.get('total_lineages', 0)} | "
                  f"Max Depth: {ld.get('max_depth', 0)}")
            gens = ld.get("generations", {})
            for g in sorted(gens.keys()):
                s = gens[g]
                print(f"  gen={g}: mean={s['mean_lifespan']:.1f} max={s['max_lifespan']} n={s['count']}")
            shapes = ld.get("shape_inheritance", {})
            if shapes:
                print("  Shape inheritance:")
                for h, info in sorted(shapes.items(), key=lambda kv: kv[1]["generations"], reverse=True)[:3]:
                    print(f"    {h[:8]}: {info['generations']} gens, {info['structure_count']} structs")
            print(f"  Lifespan trend: {ld.get('lifespan_trend', '?')}")

        if tick % RETRAIN_INTERVAL == 0 and tick > 0:
            X, y = [], []
            for m in memory_engine.dead_memories + list(memory_engine.memories.values()):
                if len(m.snapshots) < 10:
                    continue
                lifespan = (m.died_at or tick) - m.born_at
                feats = extract_features(m.snapshots, age=lifespan, generation=m.generation,
                                         parent_lifespan=0)
                X.append(feats)
                y.append(1 if m.died_at is not None else 0)
            if len(X) >= 20:
                death_predictor.train(X, y)

    world.bus.subscribe(EventType.TICK_END, on_tick_end_all)

    renderer = Renderer(
        world.grid, world.bus, config,
        detector=detector,
        entropy_engine=entropy,
        leaderboard_fn=build_leaderboard,
        pattern_hasher=pattern_hasher,
        lineage_data=lineage_data,
    )

    fps = 15
    try:
        with Live(renderer.build_layout(), console=renderer.console,
                  refresh_per_second=fps, screen=True) as live:
            while True:
                world.time_engine.step()
                renderer._lineage = lineage_data
                renderer.display_tick(live)
                time.sleep(1.0 / fps)
    except KeyboardInterrupt:
        pass

    print(f"\nUniverse stopped at tick {world.time_engine.tick}")
    print(f"Final: {world.grid.alive_count} cells, {world.grid.total_energy:.1f} energy")
    print(f"Structures: {detector.active_count} total, {detector.stable_count} stable")
    print(f"Memories: {len(memory_engine.memories)} active, {len(memory_engine.dead_memories)} archived")
    if lineage_data:
        print(f"Lineages: {lineage_data.get('total_lineages', 0)}, max depth: {lineage_data.get('max_depth', 0)}")
    if death_predictor.is_trained:
        print(f"Death Predictor: accuracy={death_predictor.accuracy:.2f}")
        risks = death_predictor.top_risk_factors(3)
        print(f"Top risks: {risks}")


if __name__ == "__main__":
    main()
