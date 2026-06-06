"""地图引擎 —— 网格上的太阳能梯度。"""
class MapEngine:
    def __init__(self, height: int):
        self.height = height
        self.midpoint = height // 2

    def get_multiplier(self, x: int, y: int) -> float:
        return 1.5 if y < self.midpoint else 0.5
