from sonolus.script.engine import PlayMode

from convexity.common.buckets import Buckets
from convexity.common.effect import Effects
from convexity.common.particle import Particles
from convexity.common.skin import Skin
from convexity.play.init import Init
from convexity.play.input_manager import InputManager
from convexity.play.lane import Lane
from convexity.play.note import Note, UnscoredNote
from convexity.play.stage import Stage
from convexity.play.timescale import TimescaleChange, TimescaleGroup

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
