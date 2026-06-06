"""死亡预测器的测试。"""
from src.memory_engine import MemorySnapshot
from src.death_predictor import DeathPredictor, extract_features


def make_snapshots(values, tick_start=0, interval=5):
    snaps = []
    for i, (cell_count, energy) in enumerate(values):
        snaps.append(MemorySnapshot(
            tick=tick_start + i * interval,
            cell_count=cell_count, total_energy=float(energy),
            type_composition={1: cell_count}, shape_hash="test", centroid=(0.0, 0.0),
        ))
    return snaps


class TestExtractFeatures:
    def test_extracts_all_features(self):
        snaps = make_snapshots([(5, 10), (4, 9), (3, 8), (2, 7), (1, 6)])
        features = extract_features(snaps, age=50, generation=1, parent_lifespan=40)
        for key in ["cell_count_trend", "energy_trend", "near_death_count", "age", "generation"]:
            assert key in features
        assert features["age"] == 50
        assert features["generation"] == 1

    def test_cell_count_trend_negative(self):
        snaps = make_snapshots([(10, 20), (8, 18), (6, 16), (4, 14), (2, 12),
                                (1, 10), (1, 8), (1, 6), (1, 4), (1, 2)])
        features = extract_features(snaps, age=50, generation=0, parent_lifespan=0)
        assert features["cell_count_trend"] < 0


class TestDeathPredictor:
    def test_train_and_predict(self):
        dp = DeathPredictor()
        X, y = [], []
        for i in range(60):
            if i < 30:
                snaps = make_snapshots([(s, s*2) for s in range(10, 0, -1)], tick_start=i*10)
                feats = extract_features(snaps, age=30, generation=1, parent_lifespan=25)
                X.append(feats)
                y.append(1)  # 已死亡
            else:
                snaps = make_snapshots([(5, 10)] * 10, tick_start=i*10)
                feats = extract_features(snaps, age=30, generation=1, parent_lifespan=25)
                X.append(feats)
                y.append(0)  # 已存活
        dp.train(X, y)
        assert dp.is_trained is True
        assert dp.accuracy > 0.6

    def test_predict_returns_probability(self):
        dp = DeathPredictor()
        X, y = [], []
        for i in range(60):
            if i < 30:
                snaps = make_snapshots([(s, s*2) for s in range(10, 0, -1)])
                feats = extract_features(snaps, age=30, generation=1, parent_lifespan=25)
                X.append(feats)
                y.append(1)
            else:
                snaps = make_snapshots([(5, 10)] * 10)
                feats = extract_features(snaps, age=30, generation=1, parent_lifespan=25)
                X.append(feats)
                y.append(0)
        dp.train(X, y)
        test_snaps = make_snapshots([(s, s*2) for s in range(10, 0, -1)])
        test_feats = extract_features(test_snaps, age=30, generation=1, parent_lifespan=25)
        prob = dp.predict(test_feats)
        assert 0.0 <= prob <= 1.0
        assert prob > 0.5

    def test_top_risk_factors(self):
        dp = DeathPredictor()
        X, y = [], []
        for i in range(60):
            if i < 30:
                snaps = make_snapshots([(s, 10) for s in range(10, 0, -1)])
                feats = extract_features(snaps, age=30, generation=1, parent_lifespan=25)
                X.append(feats)
                y.append(1)
            else:
                snaps = make_snapshots([(5, 10)] * 10)
                feats = extract_features(snaps, age=30, generation=1, parent_lifespan=25)
                X.append(feats)
                y.append(0)
        dp.train(X, y)
        risks = dp.top_risk_factors(3)
        assert len(risks) == 3
        # cell_count_trend 应是下降 vs 稳定状态中的首要风险因子
        assert risks[0][0] == "cell_count_trend"
