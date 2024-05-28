from collections import deque
from collections.abc import Mapping

from ballot_reader import BallotReader
from ranked_choice_display import RankedChoiceDisplay
from ranked_choice_runner import RankedChoiceRunner

ElectionMetadata = Mapping[str, str]


def _exhaust(generator):
    deque(generator, maxlen=0)


class RankedChoiceApplication:
    def __init__(self, *,
                 metadata: ElectionMetadata,
                 candidates_running: int,
                 ballot_size: int,
                 candidates_required=1,
                 threshold=0.5,
                 display_delay=1
                 ):
        self.metadata = metadata
        self.candidates_running = candidates_running
        self.ballot_size = ballot_size
        self.candidates_required = candidates_required
        self.threshold = threshold
        self.display_delay = display_delay

    def run(self):
        for title, filepath in self.metadata.items():
            election_data = BallotReader(filepath).read()

            election_runner = RankedChoiceRunner(
                election_data,
                candidates_running=self.candidates_running,
                candidates_required=self.candidates_required,
                ballot_size=self.ballot_size,
                threshold=self.threshold,
            )

            election_display = RankedChoiceDisplay(election_runner, title, delay=self.display_delay)

            election_display.run_election_display()

            print(f"Winners for {title} (candidates: {self.candidates_required}; threshold: {self.threshold}):")

            for winner in election_runner.winners:
                print(winner)
