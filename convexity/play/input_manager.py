from collections.abc import Iterable

from sonolus.script.archetype import PlayArchetype, callback
from sonolus.script.containers import VarArray
from sonolus.script.globals import level_memory
from sonolus.script.quad import Quad
from sonolus.script.runtime import Touch, time, touches
from sonolus.script.values import copy
from sonolus.script.vec import Vec2

from convexity.common.layout import Layer, Layout
from convexity.common.options import Options
from convexity.common.skin import Skin
from convexity.common.streams import Streams

input_note_indexes = level_memory(VarArray[int, 16])
used_touch_ids = level_memory(VarArray[int, 16])
empty_touch_lanes = level_memory(VarArray[float, 16])


def touch_is_used(touch: Touch) -> bool:
    return touch.id in used_touch_ids


def mark_touch_used(touch: Touch):
    used_touch_ids.set_add(touch.id)


def mark_touch_id_used(touch_id: int):
    used_touch_ids.set_add(touch_id)


def add_empty_touch_lane(index: float):
    empty_touch_lanes.append(index)


def unused_touches() -> Iterable[Touch]:
    return filter(lambda touch: not touch_is_used(touch), touches())


def taps() -> Iterable[Touch]:
    return filter(lambda touch: touch.started, unused_touches())


class InputManager(PlayArchetype):
    @callback(order=-1)
    def update_sequential(self):
        input_note_indexes.clear()
        used_touch_ids.clear()
        empty_touch_lanes.clear()

    def touch(self):
        if Options.touch_lines:
            w = 0.02
            for touch in touches():
                touch_pos = copy(touch.position)
                if (Options.arc or Options.angled_hitboxes) and Options.stage_tilt > 0:
                    if touch_pos.y > Layout.vanishing_point.y:
                        touch_pos += 2 * (Layout.vanishing_point - touch_pos)
                    diff = touch_pos - Layout.vanishing_point
                    b = Layout.vanishing_point - diff * (Layout.vanishing_point.y + 2) / diff.y
                    t = Layout.vanishing_point - diff * (Layout.vanishing_point.y - 2) / diff.y
                    ort = (t - b).normalize().orthogonal()
                    layout = Quad(
                        br=b + ort * w,
                        tr=b - ort * w,
                        tl=t - ort * w,
                        bl=t + ort * w,
                    )
                    Skin.touch_line.draw(layout, z=Layer.TOUCH_LINE, a=0.2)
                else:
                    x = touch_pos.x
                    layout = Quad(
                        br=Vec2(x - w, -1),
                        tr=Vec2(x + w, -1),
                        tl=Vec2(x + w, 1),
                        bl=Vec2(x - w, 1),
                    )
                    Skin.touch_line.draw(layout, z=Layer.TOUCH_LINE, a=0.2)


class InputFinalizer(PlayArchetype):
    @callback(order=999)
    def touch(self):
        if len(empty_touch_lanes) > 0:
            Streams.empty_touch_lanes[time()] = empty_touch_lanes
