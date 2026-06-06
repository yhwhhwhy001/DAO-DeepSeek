"""时间引擎的测试。"""
from src.event_bus import EventBus, EventType
from src.time_engine import TimeEngine
from src.state_engine import StateEngine, PhysicsConfig
from src.grid import Grid
from src.cell import Cell


class TestTimeEngine:
    def test_tick_increments_counter(self):
        bus = EventBus()
        grid = Grid(width=10, height=10, boundary="toroidal")
        config = PhysicsConfig(energy_input=0)
        state = StateEngine(config, grid, bus)
        engine = TimeEngine(bus, state)

        assert engine.tick == 0
        engine.step()
        assert engine.tick == 1
        engine.step()
        assert engine.tick == 2

    def test_tick_emits_start_and_end(self):
        bus = EventBus()
        grid = Grid(width=10, height=10, boundary="toroidal")
        config = PhysicsConfig(energy_input=0)
        state = StateEngine(config, grid, bus)
        engine = TimeEngine(bus, state)

        events = []
        bus.subscribe_all(lambda e: events.append(e.type))

        engine.step()
        # Order: TICK_START first, TICK_END last
        assert events[0] == EventType.TICK_START
        assert events[-1] == EventType.TICK_END

    def test_tick_end_has_stats(self):
        bus = EventBus()
        grid = Grid(width=10, height=10, boundary="toroidal")
        grid.place(Cell(x=0, y=0, energy=5.0))
        grid.place(Cell(x=1, y=1, energy=3.0))
        config = PhysicsConfig(decay_rate=0.0, energy_input=0)
        state = StateEngine(config, grid, bus)
        engine = TimeEngine(bus, state)

        tick_end_data = []
        bus.subscribe(EventType.TICK_END, lambda e: tick_end_data.append(e.data))

        engine.step()
        assert tick_end_data[0]["tick"] == 1
        assert tick_end_data[0]["alive_count"] == 2
        assert tick_end_data[0]["total_energy"] == 8.0

    def test_run_ticks(self):
        bus = EventBus()
        grid = Grid(width=10, height=10, boundary="toroidal")
        config = PhysicsConfig(energy_input=0)
        state = StateEngine(config, grid, bus)
        engine = TimeEngine(bus, state)

        tick_ends = []
        bus.subscribe(EventType.TICK_END, lambda e: tick_ends.append(e.data["tick"]))

        engine.run(5)
        assert tick_ends == [1, 2, 3, 4, 5]
        assert engine.tick == 5
