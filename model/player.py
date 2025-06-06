import asyncio
from dataclasses import dataclass
from enum import Enum, StrEnum, auto
import os
from time import sleep
from typing import Literal
import vlc

from util import EventEmitter


class State(StrEnum):
    playing = auto()
    paused = auto()
    ended = auto()


@dataclass
class AudioPlayerStatus:
    state: State
    position: float
    length: float
    volume: float


class AudioPlayer:
    def __init__(self):
        self.player = None

        self.status_updated = EventEmitter[AudioPlayerStatus]()

    async def init(self):
        async def updater():
            while True:
                await asyncio.sleep(0.1)
                self.status_updated.emit(self.status)

        self._updater = asyncio.create_task(updater())

    def open(self, path):
        if self.player is not None:
            self.player.stop()

        path = os.path.abspath(path)
        url = "file:///" + path

        self.player = vlc.MediaPlayer(url)
        self.player.audio_set_volume(100)
        self.player.play()

    def stop(self):
        if self.player is not None:
            self.player.stop()
            self.player = None

    @property
    def paused(self) -> bool | None:
        if self.player is None:
            return

        vlc_state = self.player.get_state()
        return vlc_state == vlc.State.Paused

    @paused.setter
    def paused(self, paused: bool):
        if self.player is not None:
            if paused:
                self.player.pause()
            else:
                self.player.play()

    @property
    def position(self) -> float | None:
        if self.player is not None:
            return self.player.get_position()

    @position.setter
    def position(self, pos: float):
        if self.player is not None:
            self.player.set_position(pos)

    @property
    def volume(self) -> float | None:
        if self.player is not None:
            return self.player.audio_get_volume() / 100

    @volume.setter
    def volume(self, volume: float):
        if self.player is not None:
            self.player.audio_set_volume(int(volume * 100))

    @property
    def length(self) -> float | None:
        if self.player is not None:
            return self.player.get_length() / 1000

    @property
    def status(self) -> AudioPlayerStatus | None:
        if self.player is None:
            return None

        vlc_state = self.player.get_state()
        if vlc_state == vlc.State.Playing:
            state = State.playing
        elif vlc_state == vlc.State.Paused:
            state = State.paused
        else:
            state = State.ended

        return AudioPlayerStatus(
            state=state,
            position=self.position,
            length=self.length,
            volume=self.volume,
        )
