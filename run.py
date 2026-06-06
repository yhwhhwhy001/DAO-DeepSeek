"""DAO Genesis — Phase 1 Structure Emergence."""
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
from src.cli.renderer import Renderer


def main():
    config_path = "experiments/default.yaml"
    if len(sys.argv) > 1:
        config_path = sys.argv[1]

    with open(config_path) as f:
        config = yaml.safe_load(f)

    print(f"DAO Genesis Phase 1 — {config['experiment']['name']}")
    print(f"World: {config['world']['width']}x{config['world']['height']}, "
          f"boundary={config['world']['boundary']}, seed={config['world']['seed']}")
    print("Press Ctrl+C to stop.\n")

    world = WorldEngine(config)

    # Phase 1 engines
    detector = StructureDetector(world.grid, world.bus)
    pattern_hasher = PatternHasher()
    num_types = config["physics"]["num_types"]
    entropy = EntropyEngine(world.grid, world.bus, detector, num_types=num_types)

    # Register pattern occurrences from structures each tick
    def on_tick_end_hasher(event):
        for s in detector.get_active():
            if s.shape_hash:
                pattern_hasher.register(s.shape_hash, event.data["tick"], (0, 0))

    world.bus.subscribe(EventType.TICK_END, on_tick_end_hasher)

    renderer = Renderer(
        world.grid, world.bus, config,
        detector=detector,
        entropy_engine=entropy,
        leaderboard_fn=build_leaderboard,
        pattern_hasher=pattern_hasher,
    )

    fps = 15
    try:
        with Live(renderer.build_layout(), console=renderer.console,
                  refresh_per_second=fps, screen=True) as live:
            while True:
                world.time_engine.step()
                renderer.display_tick(live)
                time.sleep(1.0 / fps)
    except KeyboardInterrupt:
        pass

    print(f"\nUniverse stopped at tick {world.time_engine.tick}")
    print(f"Final: {world.grid.alive_count} cells, {world.grid.total_energy:.1f} energy")
    print(f"Structures: {detector.active_count} total, {detector.stable_count} stable")
    print(f"Patterns: {pattern_hasher.unique_count()} unique")


if __name__ == "__main__":
    main()
