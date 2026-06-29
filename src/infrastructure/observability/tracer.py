from __future__ import annotations

import time
import uuid
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any, Generator


@dataclass
class Span:
    trace_id: str
    span_id: str
    name: str
    start_time: float = field(default_factory=time.monotonic)
    end_time: float | None = None
    attributes: dict[str, Any] = field(default_factory=dict)
    status: str = "ok"

    def finish(self, status: str = "ok") -> None:
        self.end_time = time.monotonic()
        self.status = status

    @property
    def duration_ms(self) -> float | None:
        if self.end_time is None:
            return None
        return (self.end_time - self.start_time) * 1000


class Tracer:
    @contextmanager
    def start_span(self, name: str, attributes: dict[str, Any] | None = None) -> Generator[Span, None, None]:
        span = Span(
            trace_id=str(uuid.uuid4()),
            span_id=str(uuid.uuid4()),
            name=name,
            attributes=attributes or {},
        )
        try:
            yield span
        except Exception:
            span.finish(status="error")
            raise
        else:
            span.finish(status="ok")


_tracer = Tracer()


def get_tracer() -> Tracer:
    return _tracer
