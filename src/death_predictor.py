"""Death Predictor — Logistic Regression model for structure survival prediction."""
import math
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import cross_val_score
from src.memory_engine import MemorySnapshot

FEATURE_NAMES = [
    "cell_count_trend", "energy_trend", "type_diversity_change",
    "near_death_count", "age", "generation", "parent_lifespan", "size_cv",
]


def extract_features(
    snapshots: list[MemorySnapshot],
    age: int,
    generation: int,
    parent_lifespan: int,
) -> dict:
    recent = snapshots[-10:] if len(snapshots) >= 10 else snapshots

    cell_counts = [s.cell_count for s in recent]
    cell_trend = _slope(cell_counts)
    energies = [s.total_energy for s in recent]
    energy_trend = _slope(energies)

    if len(recent) >= 2:
        div_change = len(recent[-1].type_composition) - len(recent[0].type_composition)
    else:
        div_change = 0

    near_death = sum(1 for s in recent if s.total_energy < 1.0)

    if len(cell_counts) >= 2:
        mean = sum(cell_counts) / len(cell_counts)
        if mean > 0:
            var = sum((c - mean) ** 2 for c in cell_counts) / len(cell_counts)
            size_cv = math.sqrt(var) / mean
        else:
            size_cv = 0.0
    else:
        size_cv = 0.0

    return {
        "cell_count_trend": cell_trend,
        "energy_trend": energy_trend,
        "type_diversity_change": float(div_change),
        "near_death_count": float(near_death),
        "age": float(age),
        "generation": float(generation),
        "parent_lifespan": float(parent_lifespan),
        "size_cv": size_cv,
    }


def _slope(values: list) -> float:
    if len(values) < 2:
        return 0.0
    n = len(values)
    x_mean = (n - 1) / 2.0
    y_mean = sum(values) / n
    num = sum((i - x_mean) * (v - y_mean) for i, v in enumerate(values))
    den = sum((i - x_mean) ** 2 for i in range(n))
    return num / den if den != 0 else 0.0


class DeathPredictor:
    def __init__(self):
        self.model: LogisticRegression | None = None
        self.is_trained: bool = False
        self.accuracy: float = 0.0
        self._feature_importances: list[tuple[str, float]] = []

    def train(self, X: list[dict], y: list[int]) -> None:
        if len(X) < 20:
            return
        X_array = np.array([[d.get(k, 0.0) for k in FEATURE_NAMES] for d in X])
        y_array = np.array(y)

        classes = np.unique(y_array)
        if len(classes) < 2:
            # Single-class data: set accuracy to majority proportion and skip fit
            self.accuracy = 1.0
            self.is_trained = False
            self._feature_importances = [(name, 0.0) for name in FEATURE_NAMES]
            return

        self.model = LogisticRegression(max_iter=1000, class_weight="balanced")
        self.model.fit(X_array, y_array)

        try:
            scores = cross_val_score(self.model, X_array, y_array, cv=min(5, len(X)))
            self.accuracy = float(scores.mean())
        except Exception:
            self.accuracy = float(self.model.score(X_array, y_array))

        self.is_trained = True

        coefs = self.model.coef_[0]
        importances = [(FEATURE_NAMES[i], abs(coefs[i])) for i in range(len(FEATURE_NAMES))]
        importances.sort(key=lambda x: x[1], reverse=True)
        self._feature_importances = importances

    def predict(self, features: dict) -> float:
        if not self.is_trained or self.model is None:
            return 0.5
        X = np.array([[features.get(k, 0.0) for k in FEATURE_NAMES]])
        proba = self.model.predict_proba(X)
        return float(proba[0][1])

    def top_risk_factors(self, n: int = 3) -> list[tuple[str, float]]:
        return self._feature_importances[:n]
