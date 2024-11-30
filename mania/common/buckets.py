from sonolus.script.bucket import Bucket, JudgmentWindow, bucket, bucket_sprite, buckets
from sonolus.script.interval import Interval
from sonolus.script.text import StandardText

from mania.common.skin import Skin

"""
export const createBucketDefinition = (
    sprites: Record<'tapNote' | 'connector' | 'holdStartNote' | 'holdEndNote', { id: number }>,
) =>
    ({
        tapNote: {
            sprites: [
                {
                    id: sprites.tapNote.id,
                    x: 0,
                    y: 0,
                    w: 2,
                    h: 2,
                    rotation: -90,
                },
            ],
            unit: Text.MillisecondUnit,
        },
        holdStartNote: {
            sprites: [
                {
                    id: sprites.connector.id,
                    x: 0.5,
                    y: 0,
                    w: 2,
                    h: 5,
                    rotation: -90,
                },
                {
                    id: sprites.holdStartNote.id,
                    x: -2,
                    y: 0,
                    w: 2,
                    h: 2,
                    rotation: -90,
                },
            ],
            unit: Text.MillisecondUnit,
        },
        holdEndNote: {
            sprites: [
                {
                    id: sprites.connector.id,
                    x: -0.5,
                    y: 0,
                    w: 2,
                    h: 5,
                    rotation: -90,
                },
                {
                    id: sprites.holdEndNote.id,
                    x: 2,
                    y: 0,
                    w: 2,
                    h: 2,
                    rotation: -90,
                },
            ],
            unit: Text.MillisecondUnit,
        },
    }) as const satisfies Record<string, EngineDataBucket>

"""


@buckets
class Buckets:
    tap_note: Bucket = bucket(
        sprites=[
            bucket_sprite(
                sprite=Skin.tap_note,
                x=0,
                y=0,
                w=2,
                h=2,
                rotation=-90,
            )
        ],
        unit=StandardText.MILLISECOND_UNIT,
    )
    hold_start_note: Bucket = bucket(
        sprites=[
            bucket_sprite(
                sprite=Skin.connector,
                x=0.5,
                y=0,
                w=2,
                h=5,
                rotation=-90,
            ),
            bucket_sprite(
                sprite=Skin.hold_start_note,
                x=-2,
                y=0,
                w=2,
                h=2,
                rotation=-90,
            ),
        ],
        unit=StandardText.MILLISECOND_UNIT,
    )
    hold_end_note: Bucket = bucket(
        sprites=[
            bucket_sprite(
                sprite=Skin.connector,
                x=-0.5,
                y=0,
                w=2,
                h=5,
                rotation=-90,
            ),
            bucket_sprite(
                sprite=Skin.hold_end_note,
                x=2,
                y=0,
                w=2,
                h=2,
                rotation=-90,
            ),
        ],
        unit=StandardText.MILLISECOND_UNIT,
    )


note_judgment_window = JudgmentWindow(
    perfect=Interval(-0.05, 0.05),
    great=Interval(-0.1, 0.1),
    good=Interval(-0.15, 0.15),
)
