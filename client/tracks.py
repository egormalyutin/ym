import asyncio
from gi.repository import Gtk, Gdk

from .track import TrackWidget
from model.app import App, OpStatus


class TracksScreen:
    def __init__(self, model: App, playlist_id: str):
        self.model = model

        self.playlist = model.get_playlist(playlist_id)

        asyncio.create_task(self.playlist.load_tracks())

        self.window = Gtk.ScrolledWindow(hexpand=True, vexpand=True)

        self.box = Gtk.Box(
            hexpand=True,
            vexpand=True,
            orientation=Gtk.Orientation.VERTICAL,
            spacing=20,
        )
        self.box.add_css_class("tracks")

        self.window.set_child(self.box)

        self.spinner = Gtk.Spinner()
        self.spinner.start()

        self.box.append(self.spinner)

        self.track_widgets = []

        self.sub = self.playlist.signal_tracks.subscribe(self.loaded)

        self.gtk_root = self.window

    def loaded(self):
        if self.playlist.tracks_status != OpStatus.COMPLETED:
            return

        self.playlist.set_current()

        self.box.remove(self.spinner)

        self.tracks = []

        for id in self.playlist.tracks_ids:
            widget = TrackWidget(self.model)
            widget.update(id=id)
            self.tracks.append(widget)

            self.box.append(widget.gtk_root)
