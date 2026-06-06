"""Parameter Scanner — finds interesting parameter regimes via coarse + fine search."""
import json
import random
from pathlib import Path
from dataclasses import dataclass
from src.world_engine import WorldEngine
from src.structure_detector import StructureDetector
from src.pattern_hasher import PatternHasher

COARSE_SAMPLES = 500
COARSE_TICKS = 200
COARSE_TOP_PCT = 0.20
FINE_TICKS = 500
FINE_SEEDS = 3

DEFAULT_PARAM_RANGES = {
    "decay_rate": (0.1, 2.0),
    "drift_probability": (0.0, 0.2),
    "fission_threshold": (5.0, 20.0),
    "fusion_probability": (0.0, 0.05),
    "energy_input": (1, 20),
    "num_types": (2, 6),
}


@dataclass
class ScanResult:
    params: dict
    seed: int
    final_alive: int
    stable_structures: int
    max_structure_age: int
    unique_patterns: int
    score: float


def random_params(ranges: dict, rng: random.Random) -> dict:
    return {
        "decay_rate": round(rng.uniform(*ranges["decay_rate"]), 2),
        "drift_probability": round(rng.uniform(*ranges["drift_probability"]), 4),
        "fission_threshold": round(rng.uniform(*ranges["fission_threshold"]), 1),
        "fusion_probability": round(rng.uniform(*ranges["fusion_probability"]), 4),
        "energy_input": rng.randint(*ranges["energy_input"]),
        "num_types": rng.randint(*ranges["num_types"]),
    }


def compute_score(alive: int, stable: int, max_age: int, patterns: int) -> float:
    return stable * 3.0 + patterns * 2.0 + max_age * 0.1 + alive * 0.02


def run_single(params: dict, seed: int, ticks: int) -> ScanResult:
    config = {
        "experiment": {"name": "scan", "description": "param scan"},
        "world": {"width": 40, "height": 20, "boundary": "toroidal", "seed": seed},
        "physics": {**params},
        "initial": {"cell_count": 100, "min_energy": 3.0, "max_energy": 8.0},
        "output": {"snapshot_interval": 100, "export_dir": "data/scan_runs"},
    }
    world = WorldEngine(config)
    detector = StructureDetector(world.grid, world.bus)
    hasher = PatternHasher()

    world.time_engine.run(ticks)

    for s in detector.get_active():
        if s.shape_hash:
            hasher.register(s.shape_hash, world.time_engine.tick, (0, 0))

    stable = detector.stable_count
    max_age = max((s.age for s in detector.get_active()), default=0)
    return ScanResult(
        params=params, seed=seed,
        final_alive=world.grid.alive_count,
        stable_structures=stable,
        max_structure_age=max_age,
        unique_patterns=hasher.unique_count(),
        score=compute_score(world.grid.alive_count, stable, max_age, hasher.unique_count()),
    )


def coarse_scan(base_seed: int = 42) -> list[ScanResult]:
    rng = random.Random(base_seed)
    results = []
    for i in range(COARSE_SAMPLES):
        params = random_params(DEFAULT_PARAM_RANGES, rng)
        result = run_single(params, rng.randint(1, 10000), COARSE_TICKS)
        results.append(result)
    results.sort(key=lambda r: r.score, reverse=True)
    return results


def fine_scan(top_results: list[ScanResult]) -> list[ScanResult]:
    results = []
    for base in top_results:
        for seed_offset in range(FINE_SEEDS):
            seed = base.seed + seed_offset * 100
            result = run_single(base.params, seed, FINE_TICKS)
            results.append(result)
    results.sort(key=lambda r: r.score, reverse=True)
    return results


def main():
    print("Phase 1 Parameter Scanner")
    print(f"Coarse: {COARSE_SAMPLES} samples x {COARSE_TICKS} ticks")
    print(f"Fine: top {int(COARSE_SAMPLES * COARSE_TOP_PCT)} x {FINE_TICKS} ticks x {FINE_SEEDS} seeds")
    print()

    print("Running coarse scan...")
    coarse = coarse_scan()
    top_n = max(1, int(len(coarse) * COARSE_TOP_PCT))
    top = coarse[:top_n]

    print(f"Top {top_n} coarse results:")
    for i, r in enumerate(top[:10], 1):
        print(f"  {i}. score={r.score:.1f} stable={r.stable_structures} "
              f"age={r.max_structure_age} patterns={r.unique_patterns} "
              f"alive={r.final_alive} params={r.params}")

    print(f"\nRunning fine scan on top {top_n}...")
    fine = fine_scan(top)

    print(f"\nTop 10 fine results:")
    for i, r in enumerate(fine[:10], 1):
        print(f"  {i}. score={r.score:.1f} stable={r.stable_structures} "
              f"age={r.max_structure_age} patterns={r.unique_patterns} "
              f"seed={r.seed} alive={r.final_alive} params={r.params}")

    out_dir = Path("data/scan_results")
    out_dir.mkdir(parents=True, exist_ok=True)
    output = [{"params": r.params, "seed": r.seed, "score": r.score,
                "stable_structures": r.stable_structures,
                "max_structure_age": r.max_structure_age,
                "unique_patterns": r.unique_patterns,
                "final_alive": r.final_alive} for r in fine]
    with open(out_dir / "phase1_scan_results.json", "w") as f:
        json.dump(output, f, indent=2)
    print(f"\nResults saved to {out_dir / 'phase1_scan_results.json'}")


if __name__ == "__main__":
    main()
