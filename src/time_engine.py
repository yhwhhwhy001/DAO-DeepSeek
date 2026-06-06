"""Time Engine -- drives the tick loop with fixed phase ordering."""
from src.event_bus import EventBus, EventType
from src.state_engine import StateEngine


class TimeEngine:
    def __init__(self, bus: EventBus, state_engine: StateEngine, decision_engine=None):
        self.bus = bus
        self.state = state_engine
        self.decision_engine = decision_engine
        self._tick: int = 0

    @property
    def tick(self) -> int:
        return self._tick

    def step(self) -> None:
        self._tick += 1
        self.bus.tick = self._tick

        self.bus.publish(EventType.TICK_START, {"tick": self._tick})

        # Phase 3: Decision phase (before physics)
        if self.decision_engine is not None:
            self.decision_engine.step_all(self.state.grid, self.bus)

        self.state.apply_decay()
        self.state.apply_drift()
        self.state.apply_fission()
        self.state.apply_fusion()
        self.state.apply_injection()

        self.bus.publish(EventType.TICK_END, {
            "tick": self._tick,
            "alive_count": self.state.grid.alive_count,
            "total_energy": self.state.grid.total_energy,
        })

    def run(self, n: int) -> None:
        for _ in range(n):
            self.step()
