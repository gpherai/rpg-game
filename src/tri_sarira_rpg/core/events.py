"""Eenvoudige eventbus voor losse componentcommunicatie."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable, Iterable

EventCallback = Callable[..., None]


class EventBus:
    """Registreer luisteraars en zend events naar gekoppelde systemen."""

    def __init__(self) -> None:
        self._listeners: defaultdict[str, list[EventCallback]] = defaultdict(list)

    def subscribe(self, event_name: str, callback: EventCallback) -> None:
        """Registreer een callback voor het opgegeven event."""

        self._listeners[event_name].append(callback)

    def unsubscribe(self, event_name: str, callback: EventCallback) -> None:
        """Verwijder een callback indien geregistreerd."""

        if callback in self._listeners.get(event_name, []):
            self._listeners[event_name].remove(callback)

    def emit(self, event_name: str, *args, **kwargs) -> None:
        """Roep alle listeners voor een event aan."""

        for callback in list(self._listeners.get(event_name, [])):
            callback(*args, **kwargs)

    def listeners(self, event_name: str) -> Iterable[EventCallback]:
        """Geef huidige listeners voor inspectie/debug."""

        return tuple(self._listeners.get(event_name, ()))


__all__ = ["EventBus"]
