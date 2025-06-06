from typing import Self
from gi.repository import Gtk, Gdk

from util import EventEmitter

_navigator = None


def _gtk(w):
    if isinstance(w, Gtk.Widget):
        return w
    else:
        return w.gtk_root


class Navigator(Gtk.Stack):
    def __init__(self):
        super().__init__()

        global _navigator
        _navigator = self

        self.stack = []

        self.set_transition_type(Gtk.StackTransitionType.SLIDE_RIGHT)

        self.signal_update = EventEmitter()

    def get() -> Self:
        global _navigator
        return _navigator

    def push(self, widget):
        self.stack.append(widget)

        self.add_child(_gtk(widget))
        self.set_visible_child(_gtk(widget))

        self.signal_update.emit()

    def pop(self):
        widget = self.stack.pop()

        self.set_visible_child(_gtk(self.stack[-1]))
        self.remove(_gtk(widget))

        self.signal_update.emit()
