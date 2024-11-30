from collections.abc import Iterable

from sonolus.script.archetype import PlayArchetype, callback
from sonolus.script.containers import VarArray
from sonolus.script.globals import level_memory
from sonolus.script.runtime import Touch, touches

used_touch_ids = level_memory(VarArray[int, 16])


def touch_is_used(touch: Touch) -> bool:
    return touch.id in used_touch_ids


def mark_touch_used(touch: Touch):
    used_touch_ids.set_add(touch.id)


def unused_touches() -> Iterable[Touch]:
    return filter(lambda touch: not touch_is_used(touch), touches())


def taps_in_hitbox(hitbox) -> Iterable[Touch]:
    return filter(
        lambda touch: hitbox.contains_point(touch.position) and touch.started,
        unused_touches(),
    )


class InputManager(PlayArchetype):
    @callback(order=-1)
    def touch(self):
        used_touch_ids.clear()
