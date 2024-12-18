from math import floor

from sonolus.script.archetype import PreviewArchetype, callback
from sonolus.script.printing import PrintColor, PrintFormat
from sonolus.script.quad import Rect
from sonolus.script.runtime import (
    preview_ui as ui,
)
from sonolus.script.runtime import (
    preview_ui_configs as ui_configs,
)
from sonolus.script.runtime import (
    screen,
)
from sonolus.script.vec import Vec2

from convexity.common.layout import Layer, init_layout
from convexity.common.skin import Skin
from convexity.preview.layout import (
    COVER_ALPHA,
    LINE_ALPHA,
    Y_B,
    Y_T,
    PreviewData,
    PreviewLayout,
    init_preview_layout,
    left_line_layout,
    print_at_time,
)


class Init(PreviewArchetype):
    @callback(order=1)
    def preprocess(self):
        init_layout()
        init_preview_layout()

        ui.menu.update(
            anchor=screen().tl + Vec2(0.05, -0.05),
            pivot=Vec2(0, 1),
            dimensions=Vec2(0.15, 0.15) * ui_configs.menu.scale,
            rotation=0,
            alpha=ui_configs.menu.alpha,
            background=True,
        )
        ui.progress.update(
            anchor=screen().bl + Vec2(0.05, 0.05),
            pivot=Vec2(0, 0),
            dimensions=Vec2(screen().w - 0.1, y=0.15 * ui_configs.progress.scale),
            rotation=0,
            alpha=ui_configs.progress.alpha,
            background=True,
        )

    def render(self):
        for col in range(PreviewLayout.column_count):
            l = col * PreviewLayout.column_width - screen().w / 2
            r = l + PreviewLayout.column_width
            Skin.cover.draw(
                Rect(
                    l=l,
                    r=r,
                    b=-1,
                    t=Y_B,
                ),
                z=Layer.COVER,
                a=COVER_ALPHA,
            )
            Skin.cover.draw(
                Rect(
                    l=l,
                    r=r,
                    b=Y_T,
                    t=1,
                ),
                z=Layer.COVER,
                a=COVER_ALPHA,
            )
        for time in range(floor(PreviewData.last_time) + 1):
            print_at_time(
                time,
                time,
                fmt=PrintFormat.TIME,
                decimal_places=0,
                color=PrintColor.CYAN,
                side="left",
            )
            Skin.time_line.draw(
                left_line_layout(time),
                z=Layer.TIME_LINE,
                a=LINE_ALPHA,
            )
