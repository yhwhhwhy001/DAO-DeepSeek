"""排行榜 —— 按稳定性、复杂度、多样性和模式流行度对结构进行排名。"""


def score_structure(
    age: int, max_age: int,
    size: float, max_size: float,
    type_count: int, num_types: int,
    pattern_occurrences: int, max_pattern_occs: int,
) -> float:
    stability = age / max_age if max_age > 0 else 0.0
    complexity = size / max_size if max_size > 0 else 0.0
    diversity = type_count / num_types if num_types > 0 else 0.0
    pattern = pattern_occurrences / max_pattern_occs if max_pattern_occs > 0 else 0.0
    return stability * 0.35 + complexity * 0.25 + diversity * 0.25 + pattern * 0.15


def build_leaderboard(
    structures: list[dict],
    pattern_occurrences: dict[str, int],
    num_types: int = 4,
    top_n: int = 5,
) -> list[dict]:
    if not structures:
        return []

    max_age = max(s["age"] for s in structures)
    max_size = max(s["size"] for s in structures)
    max_pattern = max(pattern_occurrences.values()) if pattern_occurrences else 1

    scored = []
    for s in structures:
        shape_hash = s.get("shape_hash", "")
        score = score_structure(
            age=s["age"], max_age=max_age,
            size=s["size"], max_size=max_size,
            type_count=s.get("type_count", 1), num_types=num_types,
            pattern_occurrences=pattern_occurrences.get(shape_hash, 0),
            max_pattern_occs=max_pattern,
        )
        scored.append({**s, "score": score})

    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored[:top_n]
