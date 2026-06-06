"""EventBus -- decoupled pub/sub between engines."""
from dataclasses import dataclass
from enum import Enum, auto
from typing import Any, Callable


class EventType(Enum):
    TICK_START = auto()
    TICK_END = auto()
    CELL_CREATED = auto()
    CELL_DESTROYED = auto()
    STATE_CHANGED = auto()
    STRUCTURE_FORMED = auto()
    STRUCTURE_LOST = auto()
    STRUCTURE_STABLE = auto()
    TREND_CHANGED = auto()


@dataclass
class Event:
    type: EventType
    data: dict[str, Any]
    tick: int = 0


Handler = Callable[[Event], None]


class EventBus:
    def __init__(self):
        self._subscribers: dict[EventType, list[Handler]] = {t: [] for t in EventType}
        self._wildcard: list[Handler] = []
        self.tick: int = 0

    def subscribe(self, event_type: EventType, handler: Handler) -> None:
        self._subscribers[event_type].append(handler)

    def subscribe_all(self, handler: Handler) -> None:
        self._wildcard.append(handler)

    def unsubscribe(self, event_type: EventType, handler: Handler) -> None:
        try:
            self._subscribers[event_type].remove(handler)
        except ValueError:
            pass

    def publish(self, event_type: EventType, data: dict[str, Any]) -> None:
        event = Event(type=event_type, data=data, tick=self.tick)
        for h in self._subscribers[event_type]:
            h(event)
        for h in self._wildcard:
            h(event)
