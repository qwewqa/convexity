from sonolus.script.engine import WatchMode

from convexity.common.buckets import Buckets
from convexity.common.effect import Effects
from convexity.common.particle import Particles
from convexity.common.skin import Skin
from convexity.watch.init import Init
from convexity.watch.lane import Lane
from convexity.watch.note import Note, UnscoredNote
from convexity.watch.stage import Stage
from convexity.watch.timescale import TimescaleChange, TimescaleGroup
from convexity.watch.update_spawn import update_spawn

watch_mode = WatchMode(
    archetypes=[
        Init,
        Stage,
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
    update_spawn=update_spawn,
)
