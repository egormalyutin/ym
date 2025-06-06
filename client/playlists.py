import asyncio
from gi.repository import Gtk

from client.navigator import Navigator
from client.tracks import TracksScreen

from .track import TrackWidget
from model.app import App, OpStatus


class PlaylistsScreen:
    def __init__(self, model: App):
        self.model = model

        self.window = Gtk.ScrolledWindow(hexpand=True, vexpand=True)

        self.box = Gtk.Box(
            hexpand=True,
            vexpand=True,
            orientation=Gtk.Orientation.VERTICAL,
            spacing=20,
        )

        self.box.add_css_class("playlists")

        self.window.set_child(self.box)

        self.spinner = Gtk.Spinner()
        self.spinner.start()

        self.box.append(self.spinner)

        asyncio.create_task(model.get_playlists())
        self.sub = model.playlists_notifier.subscribe(self.loaded)

        self.gtk_root = self.window

    def create_open_playlist(self, id):
        return lambda *_: Navigator.get().push(TracksScreen(self.model, id))

    def loaded(self):
        if self.model.playlists_status != OpStatus.COMPLETED:
            return

        self.box.remove(self.spinner)

        box = Gtk.FlowBox()

        for playlist in self.model.playlists:
            widget = Gtk.Button(label=playlist.title)
            widget.connect("clicked", self.create_open_playlist(playlist.id))
            box.append(widget)

        self.box.append(box)
