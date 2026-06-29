from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable


class EventType(str, Enum):
    JOB_SUBMITTED = "job.submitted"
    JOB_STARTED = "job.started"
    JOB_COMPLETED = "job.completed"
    JOB_FAILED = "job.failed"
    PIPELINE_STEP_STARTED = "pipeline.step.started"
    PIPELINE_STEP_COMPLETED = "pipeline.step.completed"
    PIPELINE_STEP_FAILED = "pipeline.step.failed"
    EXECUTION_DISPATCHED = "execution.dispatched"
    EXECUTION_COMPLETED = "execution.completed"
    MODEL_RESOLVED = "model.resolved"


@dataclass
class Event:
    type: EventType
    payload: dict[str, Any] = field(default_factory=dict)
    occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


EventHandler = Callable[[Event], None]


class EventBus:
    def __init__(self) -> None:
        self._handlers: dict[EventType, list[EventHandler]] = {}

    def subscribe(self, event_type: EventType, handler: EventHandler) -> None:
        self._handlers.setdefault(event_type, []).append(handler)

    def publish(self, event: Event) -> None:
        for handler in self._handlers.get(event.type, []):
            try:
                handler(event)
            except Exception:
                pass


_event_bus = EventBus()


def get_event_bus() -> EventBus:
    return _event_bus
