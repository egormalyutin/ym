from typing import Callable, Generic, ParamSpec
from weakref import WeakSet, ref


P = ParamSpec("P")

unchanged = {"unchanged"}


def changed(data):
    return data is not unchanged


def ellipse(s, n):
    if len(s) >= n - 3:
        return s[:n-3] + "..."
    else:
        return s


class EventEmitterSubscription:
    def __init__(self, emitter, cb):
        self._emitter = ref(emitter)
        self._cb = cb

    def dispose(self):
        emitter = self._emitter()
        if emitter is not None:
            emitter._subs.remove(self)

    def __del__(self):
        self.dispose()


class EventEmitter(Generic[P]):
    def __init__(self):
        self._subs = WeakSet()

    def subscribe(self, cb: Callable[P, None]) -> EventEmitterSubscription:
        sub = EventEmitterSubscription(self, cb)
        self._subs.add(sub)
        return sub

    def emit(self, *args: P.args, **kwargs: P.kwargs):
        subs = self._subs.copy()
        for sub in subs:
            try:
                sub._cb(*args, **kwargs)
            except Exception as e:
                print(e)
                raise e
