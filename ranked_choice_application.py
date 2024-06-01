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
                 metadata_filepath: str,
                 display_delay: int | float | None = 1
                 ):
        self.output_file, self.vote_list = BallotReader(metadata_filepath).read()
        self.display_delay = display_delay

    def run(self):
        file_output: list[str] = []

        for position_data in self.vote_list:

            election_runner = RankedChoiceRunner(
                position_data.ballots,
                candidates_running=position_data.num_candidates,
                candidates_required=position_data.num_winners,
                ballot_size=(1 if position_data.num_candidates <= 2 else position_data.num_candidates),
                threshold=position_data.threshold,
            )

            if self.display_delay is None:
                for run in election_runner.run_election():
                    _exhaust(run)
            else:
                election_display = RankedChoiceDisplay(
                    election_runner,
                    title=position_data.name,
                    delay=self.display_delay
                )

                election_display.run_election_display()

            file_output.append(f"Winners for {position_data.name}"
                               f"(candidates: {position_data.num_winners}; threshold: {position_data.threshold}):")

            file_output.extend(election_runner.winners)
            file_output.append("")

        with open(self.output_file, 'w') as output:
            output.write("\n".join(file_output))
