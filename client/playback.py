import asyncio
import os
from gi.repository import Gtk

from model.app import App, OpStatus
from model.player import State

from util import ellipse

dirname = os.path.dirname(__file__)


class PlaybackWidget:
    def __init__(self, app: App):
        self.app = app

        self.sub_p = self.app.playback_notifier.subscribe(self.update_track)
        self.sub_pl = self.app.player.status_updated.subscribe(
            self.update_status)

        self.gtk_root = self.revealer = Gtk.Revealer()

        self.revealer.set_transition_type(Gtk.RevealerTransitionType.SLIDE_UP)

        box = Gtk.CenterBox()
        self.revealer.set_child(box)

        box.add_css_class("playback")

        # track info
        track_box = Gtk.Box(
            orientation=Gtk.Orientation.HORIZONTAL,
            spacing=10,
        )

        box.set_start_widget(track_box)

        # track cover
        self.cover = Gtk.Image()
        self.cover.add_css_class("playback-cover")
        self.cover.set_overflow(True)
        self.cover.set_size_request(100, 100)

        track_box.append(self.cover)

        # title and artist
        track_text_box = Gtk.Box(
            halign=Gtk.Align.START,
            valign=Gtk.Align.CENTER,
            orientation=Gtk.Orientation.VERTICAL,
            spacing=5,
        )

        # title
        self.track_name = Gtk.Label(
            halign=Gtk.Align.START,
        )
        self.track_name.add_css_class("playback-track-name")

        track_text_box.append(self.track_name)

        # artist
        self.track_artist = Gtk.Label(
            halign=Gtk.Align.START,
        )
        self.track_artist.add_css_class("playback-track-artist")

        track_text_box.append(self.track_artist)

        track_box.append(track_text_box)

        # ctl
        ctl_box = Gtk.Box(
            halign=Gtk.Align.CENTER,
            valign=Gtk.Align.CENTER,
            orientation=Gtk.Orientation.VERTICAL,
            spacing=20,
        )

        box.set_center_widget(ctl_box)

        ctl_box.add_css_class("playback-box")

        buttons_box = Gtk.Box(
            orientation=Gtk.Orientation.HORIZONTAL,
            halign=Gtk.Align.CENTER,
            valign=Gtk.Align.CENTER,
            hexpand=True,
            spacing=10
        )

        self.prev_btn = Gtk.Button(valign=Gtk.Align.CENTER)
        self.prev_btn.add_css_class("circular")
        self.prev_btn.add_css_class("playback-button-prev")
        self.prev_btn.set_icon_name("go-previous")
        self.prev_btn.connect("clicked", self.prev)
        buttons_box.append(self.prev_btn)

        self.play_btn = Gtk.Button(valign=Gtk.Align.CENTER)
        self.play_btn.add_css_class("circular")
        self.play_btn.add_css_class("playback-button-play")
        self.play_btn.set_icon_name("media-playback-start")
        self.play_btn.connect("clicked", self.trigger_play)
        buttons_box.append(self.play_btn)

        self.next_btn = Gtk.Button(valign=Gtk.Align.CENTER)
        self.next_btn.add_css_class("circular")
        self.next_btn.add_css_class("playback-button-next")
        self.next_btn.set_icon_name("go-next")
        self.next_btn.connect("clicked", self.next)
        buttons_box.append(self.next_btn)

        ctl_box.append(buttons_box)

        self.scale_box = Gtk.Box()

        self.scale = Gtk.Scale.new_with_range(
            Gtk.Orientation.HORIZONTAL, 0., 1., 0.01)

        self.scale_box.append(self.scale)

        click = Gtk.GestureClick()
        click.connect("pressed", self.scale_pressed)
        click.connect("released", self.scale_released)
        click.set_propagation_phase(Gtk.PropagationPhase.CAPTURE)
        self.scale_box.add_controller(click)

        self.scale_active = False

        self.scale.set_size_request(300, -1)

        ctl_box.append(self.scale_box)

        self.spinner = Gtk.Spinner()
        self.spinner.start()

    async def update_cover(self):
        if self.app.playing_track is None:
            return

        path = await self.app.get_track_cover_path(self.app.playing_track)
        self.cover.set_from_file(path)

    def update_track(self):
        if self.app.playing_track is None:
            self.revealer.set_reveal_child(False)
            return
        else:
            self.revealer.set_reveal_child(True)

        track = self.app.get_track(self.app.playing_track)

        asyncio.create_task(self.update_cover())

        self.update_status()

        title = ellipse(track.title, 20)
        self.track_name.set_label(title)

        artists = ellipse(", ".join(a for _, a in track.artists), 20)
        self.track_artist.set_label(artists)

        self.prev_btn.set_sensitive(self.app.can_move(-1))
        self.next_btn.set_sensitive(self.app.can_move(1))

    def update_status(self, *_):
        status = self.app.player.status

        if status is None:
            if self.app.playing_track is None:
                self.revealer.set_reveal_child(False)

            self.play_btn.set_child(self.spinner)
            return

        if status.state == State.ended:
            self.revealer.set_reveal_child(False)
            return
        else:
            self.revealer.set_reveal_child(True)

        if not self.scale_active:
            Gtk.Range.set_value(self.scale, status.position)

        if self.app.playing_track_status == OpStatus.PENDING:
            self.play_btn.set_child(self.spinner)
        elif status.state is State.playing:
            self.play_btn.set_icon_name("media-playback-pause")
        else:
            self.play_btn.set_icon_name("media-playback-start")

    def scale_pressed(self, *_):
        self.scale_active = True

    def scale_released(self, *_):
        self.app.player.position = self.scale.get_value()
        self.scale_active = False

    def trigger_play(self, _):
        self.app.player.paused = not self.app.player.paused

    def prev(self, *_):
        asyncio.create_task(self.app.prev())

    def next(self, *_):
        asyncio.create_task(self.app.next())
