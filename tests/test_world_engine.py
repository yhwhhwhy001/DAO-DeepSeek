"""Tests for World Engine."""
import yaml
from pathlib import Path
from src.world_engine import WorldEngine


CONFIG_YAML = """
experiment:
  name: "test"
  description: "test run"

world:
  width: 20
  height: 10
  boundary: "toroidal"
  seed: 42

physics:
  decay_rate: 1.0
  drift_probability: 0.0
  fission_threshold: 10.0
  fusion_probability: 0.0
  energy_input: 0
  num_types: 4

initial:
  cell_count: 50
  min_energy: 3.0
  max_energy: 8.0

output:
  snapshot_interval: 100
  export_dir: "data/test_runs"
"""


class TestWorldEngine:
    def test_init_from_config_dict(self):
        config = yaml.safe_load(CONFIG_YAML)
        world = WorldEngine(config)
        assert world.grid.width == 20
        assert world.grid.height == 10
        assert world.grid.alive_count == 50
        assert world.time_engine.tick == 0

    def test_init_places_cells_within_energy_range(self):
        config = yaml.safe_load(CONFIG_YAML)
        world = WorldEngine(config)
        for cell in world.grid.all_cells:
            assert 3.0 <= cell.energy <= 8.0

    def test_run_ticks_produces_stats(self):
        config = yaml.safe_load(CONFIG_YAML)
        world = WorldEngine(config)
        stats = world.run(10)
        assert len(stats) == 10
        assert all("tick" in s for s in stats)
        assert all("alive_count" in s for s in stats)
        assert all("total_energy" in s for s in stats)

    def test_stats_show_energy_decline(self):
        config = yaml.safe_load(CONFIG_YAML)
        world = WorldEngine(config)
        stats = world.run(5)
        # Without energy input, energy should decline (decay)
        assert stats[-1]["total_energy"] <= stats[0]["total_energy"]

    def test_load_from_yaml_file(self, tmp_path):
        config_path = tmp_path / "test.yaml"
        config_path.write_text(CONFIG_YAML)
        world = WorldEngine.from_yaml(str(config_path))
        assert world.grid.width == 20
        assert world.grid.alive_count == 50
