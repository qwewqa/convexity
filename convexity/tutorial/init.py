from sonolus.script.runtime import (
    screen,
)
from sonolus.script.runtime import (
    tutorial_ui as ui,
)
from sonolus.script.runtime import (
    tutorial_ui_configs as ui_configs,
)
from sonolus.script.vec import Vec2

from convexity.common.layout import init_layout


def preprocess():
    init_layout()

    ui.menu.update(
        anchor=screen().tr + Vec2(-0.05, -0.05),
        pivot=Vec2(1, 1),
        dimensions=Vec2(0.15, 0.15) * ui_configs.menu.scale,
        rotation=0,
        alpha=ui_configs.menu.alpha,
        background=True,
    )
    ui.previous.update(
        anchor=Vec2(screen().l + 0.05, 0),
        pivot=Vec2(0, 0.5),
        dimensions=Vec2(0.15, 0.15) * ui_configs.navigation.scale,
        rotation=0,
        alpha=ui_configs.navigation.alpha,
        background=True,
    )
    ui.next.update(
        anchor=Vec2(screen().r - 0.05, 0),
        pivot=Vec2(1, 0.5),
        dimensions=Vec2(0.15, 0.15) * ui_configs.navigation.scale,
        rotation=0,
        alpha=ui_configs.navigation.alpha,
        background=True,
    )
    ui.instruction.update(
        anchor=Vec2(0, 0.2),
        pivot=Vec2(0.5, 0.5),
        dimensions=Vec2(1.2, 0.15) * ui_configs.instruction.scale,
        rotation=0,
        alpha=ui_configs.instruction.alpha,
        background=True,
    )
