import asyncio
from glob import glob
import os
from weakref import ref

from gi.repository import Gtk, Gdk

from util import changed, unchanged


class TrackWidget:
    def __init__(self, app):
        self.app = app

        self.gtk_root = box = Gtk.Box(
            valign=Gtk.Align.CENTER,
            hexpand=True,
            orientation=Gtk.Orientation.HORIZONTAL,
            spacing=20,
        )

        weak_self = ref(self)
        click = Gtk.GestureClick()
        click.connect("released", lambda *_: weak_self().play())
        box.add_controller(click)

        box.set_cursor(Gdk.Cursor.new_from_name("pointer"))

        box.add_css_class("track")

        self.cover = Gtk.Image()
        self.cover.set_size_request(50, 50)
        box.append(self.cover)

        info_box = Gtk.Box(
            halign=Gtk.Align.START,
            valign=Gtk.Align.CENTER,
            hexpand=True,
            orientation=Gtk.Orientation.VERTICAL,
            spacing=5,
        )

        self.title = Gtk.Label(halign=Gtk.Align.START, max_width_chars=30)
        info_box.append(self.title)

        self.artist = Gtk.Label(halign=Gtk.Align.START, max_width_chars=30)
        self.artist.add_css_class("artist")
        info_box.append(self.artist)

        box.append(info_box)

    async def update_cover(self):
        path = await self.app.get_track_cover_path(self.id)
        if path is not None:
            self.cover.set_from_file(path)

    def update(self, id=unchanged):
        if not changed(id):
            return

        self.id = id

        track = self.app.get_track(id)

        self.title.set_label(track.title)
        self.artist.set_label(", ".join(a for _, a in track.artists))

        asyncio.create_task(self.update_cover())

    def play(self):
        asyncio.create_task(self.app.play(self.id))
