from sonolus.script.archetype import PreviewArchetype, StandardArchetypeName, StandardImport, entity_data, imported
from sonolus.script.printing import PrintColor, PrintFormat
from sonolus.script.timing import beat_to_starting_beat, beat_to_time

from convexity.common.layout import Layer
from convexity.common.skin import Skin
from convexity.preview.layout import LINE_ALPHA, PreviewData, inner_line_layout, left_right_line_layout, print_at_time


class BpmChange(PreviewArchetype):
    name = StandardArchetypeName.BPM_CHANGE

    beat: StandardImport.BEAT
    bpm: StandardImport.BPM
    meter: int = imported()

    time: float = entity_data()

    def preprocess(self):
        self.time = beat_to_time(self.beat)

    def render(self):
        Skin.bpm_change_line.draw(
            left_right_line_layout(self.time),
            z=Layer.BPM_CHANGE_LINE + self.time / 1000,
            a=LINE_ALPHA,
        )
        print_at_time(
            self.bpm,
            self.time,
            fmt=PrintFormat.BPM,
            decimal_places=1,
            color=PrintColor.PURPLE,
            side="right",
        )
        beat = self.beat + self.meter
        if self.meter < 1:
            return
        while beat_to_starting_beat(beat) == self.beat and beat <= PreviewData.last_beat:
            Skin.measure_line.draw(
                inner_line_layout(beat_to_time(beat)),
                z=Layer.MEASURE_LINE - beat_to_time(beat) / 100,
                a=LINE_ALPHA,
            )
            beat += self.meter
