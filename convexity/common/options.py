from __future__ import annotations

from enum import IntEnum

from sonolus.script.options import options, select_option, slider_option, toggle_option
from sonolus.script.text import StandardText


class SoflanMode(IntEnum):
    DEFAULT = 0
    DISABLED = 1
    PULSE = 2
    WAVE = 3


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
        scope=None,
        default=0.0,
        min=0.0,
        max=5.0,
        step=0.05,
        standard=True,
    )
    window_size: float = slider_option(
        name="Judgment Window Size",
        scope=None,
        default=1.0,
        min=0.2,
        max=2.0,
        step=0.05,
        unit=StandardText.PERCENTAGE_UNIT,
        standard=True,
    )
    hidden: float = slider_option(
        name=StandardText.HIDDEN,
        scope=None,
        default=0,
        min=0,
        max=0.8,
        step=0.05,
        unit=StandardText.PERCENTAGE_UNIT,
        standard=True,
    )
    auto_release_holds: bool = toggle_option(
        name="Auto Release Holds",
        scope=None,
        default=False,
        standard=True,
    )
    boxy_sliders: bool = toggle_option(
        name="Boxy Sliders",
        scope=None,
        default=False,
        standard=True,
    )
    no_flicks: bool = toggle_option(
        name="No Flicks",
        scope=None,
        default=False,
        standard=True,
    )
    soflan_mode: SoflanMode = select_option(
        name="Soflan Mode",
        scope=None,
        default="Default",
        standard=True,
        values=[
            "Default",
            "Disabled",
            "Pulse",
            "Wave",
        ],
    )
    spread: float = slider_option(
        name="Lane Spacing",
        scope=None,
        default=0,
        min=0,
        max=1,
        step=0.05,
        unit=None,
    )
    mirror: bool = toggle_option(
        name=StandardText.MIRROR,
        scope=None,
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
    note_effect_enabled: bool = toggle_option(
        name=StandardText.NOTE_EFFECT,
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
    laneless: bool = toggle_option(
        name="Laneless",
        scope="convexity",
        default=False,
    )
    extend_lanes: bool = toggle_option(
        name="Extend Lanes",
        scope="convexity",
        default=False,
    )
