from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from enum import StrEnum, auto
from typing import Any

import aiofiles
import aiohttp

from util import EventEmitter
from .config import Config
from .storage import FileStorage
from .player import AudioPlayer

from yandex_music import ClientAsync


class OpStatus(StrEnum):
    EMPTY = auto()
    PENDING = auto()
    COMPLETED = auto()
    REJECTED = auto()


@dataclass
class PlaylistShort:
    id: str
    title: str


@dataclass
class TrackShort:
    id: str
    title: str
    albums: list[tuple[str, str]] = field(default_factory=list)
    artists: list[tuple[str, str]] = field(default_factory=list)


class Playlist:
    def __init__(self, model: App, data):
        self.model = model

        self.id = str(data.kind)
        self.data = data
        self.title = data.title

        self.tracks_status = OpStatus.EMPTY
        self.tracks_ids = []

        self.signal_tracks = EventEmitter()

    async def load_tracks(self):
        try:
            self.tracks_status = OpStatus.PENDING
            self.signal_tracks.emit()

            pl = await self.model.client.users_playlists(self.data.kind)

            self.tracks_ids = []

            for track in pl.tracks:
                self.model.tracks[str(track.id)] = track
                self.tracks_ids.append(track.id)

            self.tracks_status = OpStatus.COMPLETED
            self.signal_tracks.emit()
        except Exception as e:
            print(e)
            self.tracks_status = OpStatus.REJECTED
            self.signal_tracks.emit()

    def set_current(self):
        self.model.queue = self.tracks_ids


class LikedPlaylist:
    def __init__(self, model: App):
        self.model = model

        self.id = "liked"
        self.title = "Liked"

        self.tracks_status = OpStatus.EMPTY
        self.tracks_ids = []

        self.signal_tracks = EventEmitter()

    async def load_tracks(self):
        self.tracks_status = OpStatus.PENDING
        self.signal_tracks.emit()

        try:
            short = await self.model.client.users_likes_tracks()
            tracks = await self.model.client.tracks([track.id for track in short])

            self.tracks_ids = []

            for track in tracks:
                id = str(track.id)
                self.model.tracks[id] = track
                self.tracks_ids.append(id)

            self.tracks_status = OpStatus.COMPLETED
            self.signal_tracks.emit()

        except Exception as e:
            print(e)
            self.tracks_status = OpStatus.REJECTED
            self.signal_tracks.emit()

    def set_current(self):
        self.model.queue = self.tracks_ids


class App:
    def __init__(self, conf: Config):
        self.conf = conf

        self.client = ClientAsync(conf.ym_token)
        self.storage = FileStorage(conf.cache_dir)
        self.player = AudioPlayer()

        self.queue = []

        # playlists
        self.playlists_status = OpStatus.EMPTY
        self.playlists: list[Playlist] = []
        self.playlists_notifier = EventEmitter()

        # tracks
        self.tracks: dict[str, Any] = {}

        # covers
        self.cover_lock = asyncio.Lock()

        # player
        self.play_task = None
        self.playing_track = None
        self.playing_track_status = OpStatus.EMPTY
        self.playback_notifier = EventEmitter()

    async def init(self):
        await self.client.init()
        await self.player.init()

    def get_playlist(self, id: str):
        for pl in self.playlists:
            if pl.id == id:
                return pl

    async def get_playlists(self):
        self.playlists = [LikedPlaylist(self)]
        self.playlists_status = OpStatus.COMPLETED
        self.playlists_notifier.emit()
        return

        try:
            self.playlists_status = OpStatus.PENDING
            self.playlists_notifier.emit()

            playlists = await self.client.users_playlists_list()

            for data in playlists:
                self.playlists.append(Playlist(self, data))

            self.playlists_status = OpStatus.COMPLETED
            self.playlists_notifier.emit()

        except Exception as e:
            print(e)
            self.playlists_status = OpStatus.REJECTED
            self.playlists_notifier.emit()

    def get_track(self, id):
        track = self.tracks[id]

        return TrackShort(
            id=str(track.id),
            title=getattr(track, "title", ""),
            artists=[(str(a.id), a.name)
                     for a in getattr(track, "artists", [])],
            albums=[(str(a.id), a.title)
                    for a in getattr(track, "albums", [])],
        )

    async def get_track_cover_path(self, id):
        file_id = f"ym/track/{id}/cover"
        if self.storage.has_commited(file_id):
            return self.storage.get_path(file_id)

        if self.tracks[id].cover_uri is None:
            return None

        async with self.cover_lock:
            file_path = self.storage.create(file_id)

            await self.tracks[id].downloadCoverAsync(file_path, size="100x100")

            self.storage.commit(file_id)

            return file_path

    async def download_track(self, id):
        file_id = f"ym/track/{id}/audio"

        if self.storage.has_commited(file_id):
            return self.storage.get_path(file_id)

        file_path = self.storage.create(file_id)

        info = await self.client.tracks_download_info(id, get_direct_links=True)

        # best bitrate
        info = max(info, key=lambda i: i["bitrate_in_kbps"])

        link = info["direct_link"]

        async with aiohttp.ClientSession() as session, aiofiles.open(file_path, "wb") as file:
            async with session.get(link) as resp:
                data = await resp.read()
                await file.write(data)

        self.storage.commit(file_id)

        return file_path

    async def play(self, id):
        async def run():
            self.playing_track_status = OpStatus.PENDING

            try:
                self.playing_track = id
                self.playback_notifier.emit()

                self.player.stop()

                path = await self.download_track(id)
                self.playing_track_status = OpStatus.COMPLETED

                if self.playing_track == id:
                    self.player.open(path)
                    self.playback_notifier.emit()

            except Exception as e:
                print(e)
                self.playing_track_status = OpStatus.REJECTED
                self.playback_notifier.emit()

        if self.play_task is not None:
            self.play_task.cancel()

        self.play_task = asyncio.create_task(run())

    async def move(self, n):
        id = self.playing_track
        if id is None:
            return

        if id not in self.queue:
            return

        idx = self.queue.index(id) + n
        if idx < 0 or idx >= len(self.queue):
            return

        await self.play(self.queue[idx])

    async def prev(self):
        await self.move(-1)

    async def next(self):
        await self.move(1)

    def can_move(self, n):
        id = self.playing_track
        if id is None:
            return False

        if id not in self.queue:
            return False

        idx = self.queue.index(id) + n
        return not (idx < 0 or idx >= len(self.queue))
