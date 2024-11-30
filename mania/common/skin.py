from sonolus.script.sprite import StandardSprite, skin


@skin
class Skin:
    cover: StandardSprite.STAGE_COVER

    lane: StandardSprite.LANE
    stage_left_border: StandardSprite.STAGE_LEFT_BORDER
    stage_right_border: StandardSprite.STAGE_RIGHT_BORDER
    judgment_line: StandardSprite.JUDGMENT_LINE
    slot: StandardSprite.NOTE_SLOT

    tap_note: StandardSprite.NOTE_HEAD_CYAN

    hold_start_note: StandardSprite.NOTE_HEAD_GREEN
    hold_end_note: StandardSprite.NOTE_TAIL_GREEN

    connector: StandardSprite.NOTE_CONNECTION_GREEN
