from sonolus.script.options import options, slider_option, toggle_option
from sonolus.script.text import StandardText


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
    lane_effect_enabled: bool = toggle_option(
        name=StandardText.LANE_EFFECT,
        scope="convexity",
        default=True,
    )
    judge_line_position: float = slider_option(
        name=StandardText.JUDGELINE_POSITION,
        scope="convexity",
        default=0,
        min=-5,
        max=10,
        step=1,
        unit=None,
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
        name=StandardText.LANE_SIZE,
        scope="convexity",
        default=1,
        min=0.1,
        max=2,
        step=0.05,
        unit=StandardText.PERCENTAGE_UNIT,
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
    spread: float = slider_option(
        name="Spread",
        scope=None,
        default=0,
        min=0,
        max=1,
        step=0.05,
        unit=None,
    )
    disable_soflan: bool = toggle_option(
        name="Disable Soflan",
        scope=None,
        default=False,
        standard=True,
    )
    auto_release_holds: bool = toggle_option(
        name="Auto Release Holds",
        scope=None,
        default=False,
        standard=True,
    )
    leniency: float = slider_option(
        name="Base Leniency Override",
        scope=None,
        default=0.0,
        min=0.0,
        max=5.0,
        step=0.1,
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
    mirror: bool = toggle_option(
        name=StandardText.MIRROR,
        scope=None,
        default=False,
    )
