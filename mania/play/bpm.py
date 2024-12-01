from sonolus.script.archetype import PlayArchetype, StandardArchetypeName, StandardImport, imported


class BpmChange(PlayArchetype):
    name = StandardArchetypeName.BPM_CHANGE

    beat: StandardImport.BEAT
    bpm: StandardImport.BPM
    meter: int = imported()

    def should_spawn(self) -> bool:
        return True

    def update_parallel(self):
        self.despawn = True
