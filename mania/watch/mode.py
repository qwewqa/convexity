from sonolus.script.engine import WatchMode

from mania.common.buckets import Buckets
from mania.common.effect import Effects
from mania.common.particle import Particles
from mania.common.skin import Skin
from mania.watch.update_spawn import update_spawn

watch_mode = WatchMode(
    archetypes=[],
    skin=Skin,
    effects=Effects,
    particles=Particles,
    buckets=Buckets,
    update_spawn=update_spawn,
)
