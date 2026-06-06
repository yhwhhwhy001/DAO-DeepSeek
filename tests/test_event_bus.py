"""Tests for EventBus."""
from src.event_bus import EventBus, EventType


class TestEventBus:
    def test_lifeform_events_work(self):
        bus = EventBus()
        received = []
        bus.subscribe(EventType.LIFEFORM_DETECTED, lambda e: received.append(e))
        bus.publish(EventType.LIFEFORM_DETECTED, {"structure_id": "s1", "score": 75.0, "classification": "proto-lifeform"})
        assert len(received) == 1
    def test_subscribe_and_publish(self):
        bus = EventBus()
        received = []
        bus.subscribe(EventType.TICK_START, lambda e: received.append(e))
        bus.publish(EventType.TICK_START, {"tick": 1})
        assert len(received) == 1
        assert received[0].type == EventType.TICK_START
        assert received[0].data == {"tick": 1}

    def test_multiple_subscribers_same_event(self):
        bus = EventBus()
        results = []
        bus.subscribe(EventType.CELL_CREATED, lambda e: results.append("a"))
        bus.subscribe(EventType.CELL_CREATED, lambda e: results.append("b"))
        bus.publish(EventType.CELL_CREATED, {"cell_id": "x"})
        assert results == ["a", "b"]

    def test_unsubscribe_stops_receiving(self):
        bus = EventBus()
        results = []
        def h(e): results.append(e.data)
        bus.subscribe(EventType.TICK_END, h)
        bus.publish(EventType.TICK_END, {"tick": 1})
        bus.unsubscribe(EventType.TICK_END, h)
        bus.publish(EventType.TICK_END, {"tick": 2})
        assert len(results) == 1

    def test_publish_no_subscribers_does_not_raise(self):
        bus = EventBus()
        bus.publish(EventType.TICK_START, {"tick": 1})

    def test_wildcard_subscriber_receives_all(self):
        bus = EventBus()
        types = []
        bus.subscribe_all(lambda e: types.append(e.type))
        bus.publish(EventType.TICK_START, {})
        bus.publish(EventType.CELL_CREATED, {})
        bus.publish(EventType.TICK_END, {})
        assert types == [EventType.TICK_START, EventType.CELL_CREATED, EventType.TICK_END]

    def test_phase1_event_types_work(self):
        bus = EventBus()
        received = []
        bus.subscribe(EventType.STRUCTURE_FORMED, lambda e: received.append(e))
        bus.publish(EventType.STRUCTURE_FORMED, {"structure_id": "s1", "component_id": "c1", "cell_count": 5})
        assert len(received) == 1

    def test_event_inherits_bus_tick(self):
        bus = EventBus()
        bus.tick = 42
        received = []
        bus.subscribe(EventType.TICK_START, lambda e: received.append(e.tick))
        bus.publish(EventType.TICK_START, {})
        assert received == [42]
