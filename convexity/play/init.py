from sonolus.script.archetype import PlayArchetype, callback, imported
from sonolus.script.runtime import (
    HorizontalAlign,
    screen,
)
from sonolus.script.runtime import (
    play_ui as ui,
)
from sonolus.script.runtime import (
    play_ui_configs as ui_configs,
)
from sonolus.script.vec import Vec2

from convexity.common.init import init_buckets, init_life, init_score
from convexity.common.layout import init_layout
from convexity.common.options import Options
from convexity.play.config import PlayConfig
from convexity.play.input_manager import InputManager
from convexity.play.note import Note


class Init(PlayArchetype):
    base_leniency: float = imported()

    def spawn_order(self) -> float:
        return -1e8

    @callback(order=-1)
    def preprocess(self):
        init_buckets()
        init_score()
        init_life(Note)
        init_ui()
        init_layout()

        if Options.leniency == 0:
            PlayConfig.base_leniency = self.base_leniency
        else:
            PlayConfig.base_leniency = Options.leniency

    def update_sequential(self):
        InputManager.spawn()
        self.despawn = True


def init_ui():
    ui.menu.update(
        anchor=screen().tr + Vec2(-0.05, -0.05),
        pivot=Vec2(1, 1),
        dimensions=Vec2(0.15, 0.15) * ui_configs.menu.scale,
        rotation=0,
        alpha=ui_configs.menu.alpha,
        horizontal_align=HorizontalAlign.CENTER,
        background=True,
    )
    ui.judgment.update(
        anchor=Vec2(0, -0.25),
        pivot=Vec2(0.5, 0),
        dimensions=Vec2(0, 0.15) * ui_configs.judgment.scale,
        rotation=0,
        alpha=ui_configs.judgment.alpha,
        horizontal_align=HorizontalAlign.CENTER,
        background=False,
    )
    ui.combo_value.update(
        anchor=Vec2(screen().r * 0.7, 0),
        pivot=Vec2(0.5, 0),
        dimensions=Vec2(0, 0.2) * ui_configs.combo.scale,
        rotation=0,
        alpha=ui_configs.combo.alpha,
        horizontal_align=HorizontalAlign.CENTER,
        background=False,
    )
    ui.combo_text.update(
        anchor=Vec2(screen().r * 0.7, 0),
        pivot=Vec2(0.5, 1),
        dimensions=Vec2(0, 0.12) * ui_configs.combo.scale,
        rotation=0,
        alpha=ui_configs.combo.alpha,
        horizontal_align=HorizontalAlign.CENTER,
        background=False,
    )
    ui.primary_metric_bar.update(
        anchor=screen().tl + Vec2(0.05, -0.05),
        pivot=Vec2(0, 1),
        dimensions=Vec2(0.75, 0.15) * ui_configs.primary_metric.scale,
        rotation=0,
        alpha=ui_configs.primary_metric.alpha,
        horizontal_align=HorizontalAlign.LEFT,
        background=True,
    )
    ui.primary_metric_value.update(
        anchor=screen().tl + Vec2(0.05, -0.05) + Vec2(0.715, -0.035) * ui_configs.primary_metric.scale,
        pivot=Vec2(0, 1),
        dimensions=Vec2(0, 0.08) * ui_configs.primary_metric.scale,
        rotation=0,
        alpha=ui_configs.primary_metric.alpha,
        horizontal_align=HorizontalAlign.RIGHT,
        background=False,
    )
    ui.secondary_metric_bar.update(
        anchor=screen().tr - Vec2(0.05, 0.05) - Vec2(0.05, 0) - Vec2(0.15, 0) * ui_configs.menu.scale,
        pivot=Vec2(1, 1),
        dimensions=Vec2(0.75, 0.15) * ui_configs.secondary_metric.scale,
        rotation=0,
        alpha=ui_configs.secondary_metric.alpha,
        horizontal_align=HorizontalAlign.LEFT,
        background=True,
    )
    ui.secondary_metric_value.update(
        anchor=screen().tr
        - Vec2(0.05, 0.05)
        - Vec2(0.05, 0)
        - Vec2(0.15, 0) * ui_configs.menu.scale
        - Vec2(0.035, 0.035) * ui_configs.primary_metric.scale,
        pivot=Vec2(1, 1),
        dimensions=Vec2(0, 0.08) * ui_configs.secondary_metric.scale,
        rotation=0,
        alpha=ui_configs.secondary_metric.alpha,
        horizontal_align=HorizontalAlign.RIGHT,
        background=False,
    )
