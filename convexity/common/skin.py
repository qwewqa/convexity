from sonolus.script.sprite import RenderMode, StandardSprite, skin


@skin
class Skin:
    render_mode = RenderMode.LIGHTWEIGHT

    cover: StandardSprite.STAGE_COVER

    lane: StandardSprite.LANE
    stage_left_border: StandardSprite.STAGE_LEFT_BORDER
    stage_right_border: StandardSprite.STAGE_RIGHT_BORDER
    stage_middle: StandardSprite.STAGE_MIDDLE
    judgment_line: StandardSprite.JUDGMENT_LINE
    slot: StandardSprite.NOTE_SLOT

    tap_note: StandardSprite.NOTE_HEAD_CYAN

    hold_start_note: StandardSprite.NOTE_HEAD_GREEN
    hold_end_note: StandardSprite.NOTE_TAIL_GREEN
    hold_tick_note: StandardSprite.NOTE_TICK_GREEN

    flick_note: StandardSprite.NOTE_HEAD_RED
    flick_arrow: StandardSprite.DIRECTIONAL_MARKER_RED

    right_flick_note: StandardSprite.NOTE_HEAD_YELLOW
    right_flick_arrow: StandardSprite.DIRECTIONAL_MARKER_YELLOW

    left_flick_note: StandardSprite.NOTE_HEAD_PURPLE
    left_flick_arrow: StandardSprite.DIRECTIONAL_MARKER_PURPLE

    swing_note: StandardSprite.NOTE_HEAD_CYAN
    swing_arrow: StandardSprite.DIRECTIONAL_MARKER_CYAN

    connector: StandardSprite.GRID_GREEN

    sim_line: StandardSprite.SIMULTANEOUS_CONNECTION_NEUTRAL_SEAMLESS
