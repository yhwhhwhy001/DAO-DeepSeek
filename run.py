"""DAO Genesis — Phase 0 Universe Engine."""
import sys
import time
import yaml
from rich.live import Live
from src.world_engine import WorldEngine
from src.cli.renderer import Renderer


def main():
    config_path = "experiments/default.yaml"
    if len(sys.argv) > 1:
        config_path = sys.argv[1]

    with open(config_path) as f:
        config = yaml.safe_load(f)

    print(f"DAO Genesis Phase 0 — {config['experiment']['name']}")
    print(f"World: {config['world']['width']}x{config['world']['height']}, "
          f"boundary={config['world']['boundary']}, seed={config['world']['seed']}")
    print("Press Ctrl+C to stop.\n")

    world = WorldEngine(config)
    renderer = Renderer(world.grid, world.bus, config)

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
    print(f"Final: {world.grid.alive_count} cells, "
          f"{world.grid.total_energy:.1f} total energy")


if __name__ == "__main__":
    main()
