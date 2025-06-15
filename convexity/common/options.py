from __future__ import annotations

from enum import IntEnum

from sonolus.script.options import options, select_option, slider_option, toggle_option
from sonolus.script.text import StandardText


class SoflanMode(IntEnum):
    DEFAULT = 0
    DISABLED = 1
    PULSE = 2
    WAVE = 3
    REVERSE = 4


class LaneMode(IntEnum):
    DEFAULT = 0
    SPREAD = 1
    WAVE = 2
    CROSSOVER = 3


class ScrollMode(IntEnum):
    DEFAULT = 0
    CHAOS = 1


@options
class Options:
    speed: float = slider_option(
        name=StandardText.SPEED,
        scope=None,
        default=1,
        min=0.5,
        max=2,
        step=0.05,
        unit=StandardText.PERCENTAGE_UNIT,
        standard=True,
    )
    leniency: float = slider_option(
        name="Leniency Override",
        scope="convexity",
        default=0.0,
        min=0.0,
        max=5.0,
        step=0.05,
        standard=True,
    )
    window_size: float = slider_option(
        name="Judgment Window Size",
        scope="convexity",
        default=1.0,
        min=0.2,
        max=2.0,
        step=0.05,
        unit=StandardText.PERCENTAGE_UNIT,
        standard=True,
    )
    hidden: float = slider_option(
        name=StandardText.HIDDEN,
        scope="convexity",
        default=0,
        min=0,
        max=0.8,
        step=0.05,
        unit=StandardText.PERCENTAGE_UNIT,
        standard=True,
    )
    backspin: bool = toggle_option(
        name="Backspin",
        scope="convexity",
        default=False,
        standard=True,
    )
    blink: bool = toggle_option(
        name="Blink",
        scope="convexity",
        default=False,
        standard=True,
    )
    auto_release_holds: bool = toggle_option(
        name="Auto Release Holds",
        scope="convexity",
        default=False,
        standard=True,
    )
    tracking_sliders: bool = toggle_option(
        name="Tracking Sliders",
        scope="convexity",
        default=True,
        standard=True,
    )
    boxy_sliders: bool = toggle_option(
        name="Boxy Sliders",
        scope="convexity",
        default=False,
        standard=True,
    )
    no_flicks: bool = toggle_option(
        name="No Flicks",
        scope="convexity",
        default=False,
        standard=True,
    )
    soflan_mode: SoflanMode = select_option(
        name="Soflan Mode",
        scope="convexity",
        default="Default",
        standard=True,
        values=[
            "Default",
            "Disabled",
            "Pulse",
            "Wave",
            "Reverse",
        ],
    )
    lane_mode: LaneMode = select_option(
        name="Lane Mode",
        scope="convexity",
        default="Default",
        standard=True,
        values=[
            "Default",
            "Spread",
            "Wave",
            "Crossover",
        ],
    )
    scroll_mode: ScrollMode = select_option(
        name="Scroll Mode",
        scope="convexity",
        default="Default",
        standard=True,
        values=[
            "Default",
            "Chaos",
        ],
    )
    lane_spacing: float = slider_option(
        name="Lane Spacing",
        scope="convexity",
        default=0,
        min=0,
        max=1,
        step=0.05,
        unit=StandardText.PERCENTAGE_UNIT,
    )
    lane_width: float = slider_option(
        name="Lane Width",
        scope="convexity",
        default=1,
        min=0.5,
        max=2,
        step=0.05,
        unit=StandardText.PERCENTAGE_UNIT,
    )
    mirror: bool = toggle_option(
        name=StandardText.MIRROR,
        scope="convexity",
        default=False,
    )
    note_speed: float = slider_option(
        name=StandardText.NOTE_SPEED,
        scope="convexity",
        default=10,
        min=1,
        max=20,
        step=0.05,
        unit=None,
    )
    note_size: float = slider_option(
        name=StandardText.NOTE_SIZE,
        scope="convexity",
        default=1,
        min=0.1,
        max=2,
        step=0.05,
        unit=StandardText.PERCENTAGE_UNIT,
    )
    note_height: float = slider_option(
        name="Note Height",
        scope="convexity",
        default=1,
        min=0.1,
        max=2,
        step=0.05,
        unit=StandardText.PERCENTAGE_UNIT,
    )
    note_effect_linear_enabled: bool = toggle_option(
        name="Linear Note Effects Enabled",
        scope="convexity",
        default=True,
    )
    note_effect_circular_enabled: bool = toggle_option(
        name="Circular Note Effects Enabled",
        scope="convexity",
        default=True,
    )
    note_effect_size: float = slider_option(
        name=StandardText.NOTE_EFFECT_SIZE,
        scope="convexity",
        default=1,
        min=0.1,
        max=2,
        step=0.05,
        unit=StandardText.PERCENTAGE_UNIT,
    )
    sim_lines_enabled: bool = toggle_option(
        name=StandardText.SIMLINE,
        scope="convexity",
        default=True,
    )
    connector_alpha: float = slider_option(
        name=StandardText.CONNECTOR_ALPHA,
        scope="convexity",
        default=0.5,
        min=0,
        max=1,
        step=0.05,
        unit=StandardText.PERCENTAGE_UNIT,
    )
    arc_quality: int = slider_option(
        name="Connector Quality",
        description="Enable curved stage.",
        scope="convexity",
        default=5,
        min=1,
        max=20,
        step=1,
        unit=None,
    )
    lane_effect_enabled: bool = toggle_option(
        name=StandardText.LANE_EFFECT,
        scope="convexity",
        default=True,
    )
    judge_line_position: float = slider_option(
        name=StandardText.JUDGELINE_POSITION,
        scope="convexity",
        default=0.2,
        min=0,
        max=1,
        step=0.05,
        unit=StandardText.PERCENTAGE_UNIT,
    )
    stage_size: float = slider_option(
        name=StandardText.STAGE_SIZE,
        scope="convexity",
        default=1,
        min=0.1,
        max=2,
        step=0.05,
        unit=StandardText.PERCENTAGE_UNIT,
    )
    stage_tilt: float = slider_option(
        name=StandardText.STAGE_TILT,
        scope="convexity",
        default=0.4,
        min=0,
        max=1,
        step=0.05,
        unit=StandardText.PERCENTAGE_UNIT,
    )
    lane_length: float = slider_option(
        name="Lane Length",
        scope="convexity",
        default=10,
        min=1,
        max=40,
        step=0.5,
    )
    sfx_enabled: bool = toggle_option(
        name=StandardText.EFFECT,
        scope="convexity",
        default=True,
    )
    auto_sfx: bool = toggle_option(
        name=StandardText.EFFECT_AUTO,
        scope="convexity",
        default=False,
    )
    sticky_notes: bool = toggle_option(
        name="Sticky Notes",
        scope="convexity",
        default=False,
    )
    touch_lines: bool = toggle_option(
        name="Touch Lines",
        scope="convexity",
        default=False,
    )
    angled_hitboxes: bool = toggle_option(
        name="Angled Hitboxes",
        scope="convexity",
        default=False,
    )
    arc: bool = toggle_option(
        name="Arc",
        scope="convexity",
        default=True,
    )
    alt_side_flicks: bool = toggle_option(
        name="Alternative Side Flicks",
        scope="convexity",
        default=False,
    )
    vertical_notes: bool = toggle_option(
        name="Vertical Notes",
        scope="convexity",
        default=False,
    )
    linear_approach: float = slider_option(
        name="Linear Approach",
        scope="convexity",
        default=0,
        min=0,
        max=1,
        step=0.05,
        unit=StandardText.PERCENTAGE_UNIT,
    )
    slot_judge_line: bool = toggle_option(
        name="Slot Judge Line",
        scope="convexity",
        default=False,
    )
    laneless: bool = toggle_option(
        name="Laneless",
        description="Hide lane dividers.",
        scope="convexity",
        default=False,
    )
    extend_lanes: bool = toggle_option(
        name="Extend Lanes",
        description="Extend lanes beyond where notes spawn.",
        scope="convexity",
        default=False,
    )
