from sonolus.script.archetype import StandardArchetypeName, StandardImport, WatchArchetype, imported


class BpmChange(WatchArchetype):
    name = StandardArchetypeName.BPM_CHANGE

    beat: StandardImport.BEAT
    bpm: StandardImport.BPM
    meter: int = imported()

    def spawn_time(self) -> float:
        return -1

    def despawn_time(self) -> float:
        return -1
