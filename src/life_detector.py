"""Life Detector — 5-dimension Life Score computation and classification."""
import math
from dataclasses import dataclass, field
from src.event_bus import EventBus, EventType


def clamp(v: float, lo: float = 0.0, hi: float = 20.0) -> float:
    return max(lo, min(hi, v))


def compute_survival_score(age: int, is_stable: bool, generation: int) -> float:
    s = min(age / 100, 1.0) * 10
    if is_stable:
        s += 5
    s += min(generation, 5)
    return clamp(s)


def compute_memory_score(data: dict) -> float:
    s = min(data.get("snapshot_count", 0) / 50, 1.0) * 8
    s += min(data.get("event_types", 0) / 5, 1.0) * 6
    if data.get("has_parent") and data.get("has_children"):
        s += 6
    return clamp(s)


def compute_replication_score(data: dict) -> float:
    children = len(data.get("fission_children", []))
    s = min(children / 5, 1.0) * 12
    max_gen = data.get("max_lineage_generation", 0)
    s += min(max_gen / 3, 1.0) * 8
    return clamp(s)


def compute_decision_score(data: dict) -> float:
    total = max(data.get("total_actions", 1), 1)
    non_stay = data.get("non_stay", 0)
    s = (non_stay / total) * 10
    s += min(data.get("q_entries", 0) / 20, 1.0) * 6
    s += min(data.get("unique_actions", 0) / 5, 1.0) * 4
    return clamp(s)


def compute_adaptation_score(data: dict) -> float:
    snapshots = data.get("snapshots", [])
    events = data.get("events", [])
    if len(snapshots) < 5:
        return 10.0

    energies = []
    for s in snapshots:
        if isinstance(s, dict):
            energies.append(s.get("total_energy", 0.0))
        else:
            energies.append(getattr(s, 'total_energy', 0.0))

    if len(energies) < 2:
        return 10.0

    mean_e = sum(energies) / len(energies)
    if mean_e > 0:
        var = sum((e - mean_e) ** 2 for e in energies) / len(energies)
        cv = math.sqrt(var) / mean_e
        s = (1.0 - min(cv, 1.0)) * 10
    else:
        s = 0.0

    near_death = 0
    for e in events:
        et = e.get("event_type") if isinstance(e, dict) else getattr(e, 'event_type', '')
        if et == "near_death":
            near_death += 1
    if near_death == 0:
        s += 6
    else:
        s += 3

    if len(energies) >= 3:
        n = len(energies)
        x_mean = (n - 1) / 2.0
        y_mean = mean_e
        num = sum((i - x_mean) * (e - y_mean) for i, e in enumerate(energies))
        den = sum((i - x_mean) ** 2 for i in range(n))
        trend = abs(num / den) if den != 0 else 999.0
        if trend < 0.1:
            s += 4
        elif trend < 0.3:
            s += 2

    return clamp(s)


@dataclass
class LifeAssessment:
    structure_id: str
    tick: int
    scores: dict
    total_score: float
    classification: str


@dataclass
class LifeformRecord:
    structure_id: str
    first_detected_at: int | None = None
    first_true_at: int | None = None
    peak_score: float = 0.0
    peak_tick: int = 0
    assessments: list = field(default_factory=list)
    status: str = "alive"


class LifeDetector:
    def __init__(self, bus: EventBus | None = None):
        self.bus = bus
        self.records: dict[str, LifeformRecord] = {}

    def assess(self, structure_id: str, **kwargs) -> dict:
        age = kwargs.get("age", 0)
        is_stable = kwargs.get("is_stable", False)
        generation = kwargs.get("generation", 0)
        memory_data = kwargs.get("memory_data", {})
        decision_data = kwargs.get("decision_data", {})
        adaptation_data = kwargs.get("adaptation_data", {})

        survival = compute_survival_score(age, is_stable, generation)
        memory = compute_memory_score(memory_data)
        replication = compute_replication_score(memory_data)
        decision = compute_decision_score(decision_data)
        adaptation = compute_adaptation_score(adaptation_data)

        total = survival + memory + replication + decision + adaptation
        if total >= 80:
            classification = "true-lifeform"
        elif total >= 60:
            classification = "proto-lifeform"
        else:
            classification = "inert"

        return {
            "structure_id": structure_id,
            "scores": {"survival": survival, "memory": memory,
                       "replication": replication, "decision": decision,
                       "adaptation": adaptation},
            "total_score": total,
            "classification": classification,
        }

    def evaluate(self, structure_id: str, tick: int, **kwargs) -> dict:
        result = self.assess(structure_id, **kwargs)
        result["tick"] = tick

        if structure_id not in self.records:
            self.records[structure_id] = LifeformRecord(structure_id=structure_id)
        record = self.records[structure_id]
        classification = result["classification"]

        if classification != "inert":
            if record.first_detected_at is None:
                record.first_detected_at = tick
                if self.bus:
                    self.bus.publish(EventType.LIFEFORM_DETECTED, {
                        "structure_id": structure_id,
                        "score": result["total_score"],
                        "classification": classification,
                    })
            if classification == "true-lifeform" and record.first_true_at is None:
                record.first_true_at = tick
                if self.bus:
                    self.bus.publish(EventType.LIFEFORM_ADVANCED, {
                        "structure_id": structure_id,
                        "old_class": "proto-lifeform",
                        "new_class": "true-lifeform",
                        "score": result["total_score"],
                    })

        if result["total_score"] > record.peak_score:
            record.peak_score = result["total_score"]
            record.peak_tick = tick

        record.assessments.append(LifeAssessment(
            structure_id=structure_id, tick=tick,
            scores=result["scores"], total_score=result["total_score"],
            classification=classification,
        ))
        if len(record.assessments) > 20:
            record.assessments = record.assessments[-20:]

        return result

    def on_structure_lost(self, structure_id: str, tick: int) -> None:
        if structure_id in self.records:
            record = self.records[structure_id]
            if record.first_detected_at is not None:
                record.status = "dead"
                if self.bus:
                    self.bus.publish(EventType.LIFEFORM_LOST, {
                        "structure_id": structure_id,
                        "peak_score": record.peak_score,
                        "lifespan": tick - (record.first_detected_at or tick),
                    })

    def get_lifeforms(self) -> list[LifeformRecord]:
        return [r for r in self.records.values()
                if r.first_detected_at is not None and r.status == "alive"]
