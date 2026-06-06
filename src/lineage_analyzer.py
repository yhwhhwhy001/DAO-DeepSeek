"""谱系分析器 —— 世代统计、生存分析、形状继承。"""
from collections import defaultdict
from src.memory_engine import Memory


class LineageAnalyzer:
    def analyze(self, active_memories: list[Memory], dead_memories: list[Memory]) -> dict:
        all_mems = list(active_memories) + list(dead_memories)
        if not all_mems:
            return {
                "generations": {},
                "max_depth": 0,
                "total_lineages": 0,
                "shape_inheritance": {},
                "lifespan_trend": "insufficient_data",
            }

        # 世代统计
        gen_stats: dict[int, dict] = {}
        for m in all_mems:
            g = m.generation
            if g not in gen_stats:
                gen_stats[g] = {"count": 0, "lifespans": [], "max_lifespan": 0}
            gen_stats[g]["count"] += 1
            lifespan = (m.died_at or m.born_at + 1) - m.born_at
            if lifespan > 0:
                gen_stats[g]["lifespans"].append(lifespan)
                if lifespan > gen_stats[g]["max_lifespan"]:
                    gen_stats[g]["max_lifespan"] = lifespan

        for g, stats in gen_stats.items():
            lifespans = stats["lifespans"]
            stats["mean_lifespan"] = sum(lifespans) / len(lifespans) if lifespans else 0
            del stats["lifespans"]

        # 最大深度
        max_depth = max((m.generation + 1 for m in all_mems), default=0)

        # 创始者计数
        founders = sum(1 for m in all_mems if m.generation == 0)

        # 形状继承：哪些形状哈希在跨代中出现
        shape_generations: dict[str, set] = defaultdict(set)
        shape_counts: dict[str, int] = defaultdict(int)
        for m in all_mems:
            for snap in m.snapshots:
                if snap.shape_hash:
                    shape_generations[snap.shape_hash].add(m.generation)
                    shape_counts[snap.shape_hash] += 1

        shape_inheritance = {}
        for h, gens in shape_generations.items():
            if len(gens) >= 2:
                shape_inheritance[h] = {
                    "generations": len(gens),
                    "gen_range": f"{min(gens)}-{max(gens)}",
                    "structure_count": shape_counts[h],
                }

        # 寿命趋势
        gen_means = [(g, stats["mean_lifespan"]) for g, stats in sorted(gen_stats.items())
                     if stats["mean_lifespan"] > 0]
        trend = "insufficient_data"
        if len(gen_means) >= 2:
            first_mean = gen_means[0][1]
            last_mean = gen_means[-1][1]
            if last_mean > first_mean * 1.1:
                trend = "increasing"
            elif last_mean < first_mean * 0.9:
                trend = "decreasing"
            else:
                trend = "stable"

        return {
            "generations": gen_stats,
            "max_depth": max_depth,
            "total_lineages": founders,
            "shape_inheritance": shape_inheritance,
            "lifespan_trend": trend,
        }
