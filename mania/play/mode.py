from sonolus.script.engine import PlayMode

from mania.common.buckets import Buckets
from mania.common.effect import Effects
from mania.common.particle import Particles
from mania.common.skin import Skin
from mania.play.init import Init
from mania.play.input_manager import InputManager
from mania.play.lane import Lane
from mania.play.note import Note, UnscoredNote
from mania.play.stage import Stage
from mania.play.timescale import TimescaleChange, TimescaleGroup

play_mode = PlayMode(
    archetypes=[
        Init,
        Stage,
        InputManager,
        Lane,
        Note,
        UnscoredNote,
        TimescaleGroup,
        TimescaleChange,
    ],
    skin=Skin,
    effects=Effects,
    particles=Particles,
    buckets=Buckets,
)
