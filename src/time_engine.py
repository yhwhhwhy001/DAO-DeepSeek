"""Time Engine -- 驱动 tick 循环，按固定阶段顺序执行。"""
from src.event_bus import EventBus, EventType
from src.state_engine import StateEngine


class TimeEngine:
    def __init__(self, bus: EventBus, state_engine: StateEngine, decision_engine=None, resource_engine=None):
        self.bus = bus
        self.state = state_engine
        self.decision_engine = decision_engine
        self.resource_engine = resource_engine
        self._tick: int = 0

    @property
    def tick(self) -> int:
        return self._tick

    def step(self) -> None:
        self._tick += 1
        self.bus.tick = self._tick

        self.bus.publish(EventType.TICK_START, {"tick": self._tick})

        # 阶段 3：决策阶段（在物理规则之前）
        if self.decision_engine is not None:
            self.decision_engine.step_all(self.state.grid, self.bus)

        self.state.apply_decay()
        self.state.apply_drift()
        self.state.apply_fission()
        self.state.apply_fusion()
        self.state.apply_injection()

        if self.resource_engine is not None:
            self.resource_engine.decay_all()

        self.bus.publish(EventType.TICK_END, {
            "tick": self._tick,
            "alive_count": self.state.grid.alive_count,
            "total_energy": self.state.grid.total_energy,
        })

    def run(self, n: int) -> None:
        for _ in range(n):
            self.step()
