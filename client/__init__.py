import sys  # noqa
sys.path.append("../")  # noqa
sys.dont_write_bytecode = True  # noqa
import gi  # noqa
gi.require_version("Gtk", "4.0")  # noqa

from glob import glob
import os

from gi.repository import Gtk, Gdk

from .playback import PlaybackWidget
from .track import TrackWidget
from .navigator import Navigator
from .tracks import TracksScreen
from .playlists import PlaylistsScreen  # noqa

from model.app import App, Config


import asyncio
from gi.events import GLibEventLoopPolicy

# Set up the GLib event loop
policy = GLibEventLoopPolicy()
asyncio.set_event_loop_policy(policy)
loop = policy.get_event_loop()

dirname = os.path.dirname(__file__)


class Window:
    def __init__(self, model: App):
        self.model = model

    def build(self, app):
        # load css
        css_provider = Gtk.CssProvider()

        css_paths = glob("**/*.css", root_dir=dirname, recursive=True)
        for path in css_paths:
            path = os.path.join(dirname, path)
            css_provider.load_from_path(path)

        Gtk.StyleContext.add_provider_for_display(
            Gdk.Display.get_default(),
            css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

        self.playback = PlaybackWidget(self.model)

        box = Gtk.Box(
            hexpand=True,
            vexpand=True,
            orientation=Gtk.Orientation.VERTICAL,
        )

        self.nav = Navigator()

        self.nav.push(PlaylistsScreen(self.model))

        box.append(self.nav)
        box.append(self.playback.gtk_root)

        window = Gtk.ApplicationWindow(application=app, title="Music")

        header_bar = Gtk.HeaderBar()
        header_bar.set_show_title_buttons(False)

        self.back_button_revealer = Gtk.Revealer()
        self.back_button_revealer.set_reveal_child(True)
        self.update_back_revealer()

        back_button = Gtk.Button()
        back_button.set_icon_name("go-previous")
        back_button.connect("clicked", lambda _: self.nav.pop())

        self.back_button_revealer.set_child(back_button)

        self.nav_sub = self.nav.signal_update.subscribe(
            self.update_back_revealer)

        header_bar.pack_start(self.back_button_revealer)

        window.set_titlebar(header_bar)

        window.set_child(box)

        return window

    def update_back_revealer(self):
        self.back_button_revealer.set_reveal_child(len(self.nav.stack) > 1)


def run_client(**config):
    model = App(Config(**config))

    loop.create_task(model.init())

    settings = Gtk.Settings.get_default()
    settings.set_property("gtk-theme-name", "WhiteSur-dark")
    app = Gtk.Application(application_id="com.egormalyutin.music")

    win = Window(model)

    app.connect("activate", lambda _: win.build(app).present())

    app.run(None)
