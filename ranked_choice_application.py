from collections import deque
from collections.abc import Generator

from ballot_reader import BallotReader
from ranked_choice_display import RankedChoiceDisplay
from ranked_choice_runner import RankedChoiceRunner


def _exhaust(generator: Generator):
    """
    Exhausts a (finite) generator.

    :param generator: the generator to exhaust
    """
    # Constructs a deque of length zero, which causes values of the generator
    # to be repeatedly added and removed
    deque(generator, maxlen=0)


class RankedChoiceApplication:
    """
    Runs a ranked choice election with a bar chart display.
    """
    def __init__(self, *,
                 config_filepath: str,
                 show_display: bool = True,
                 ):
        """
        :param config_filepath: the filepath to the config JSON file.
        :param show_display: if the election is graphically displayed or not.
        """
        self.output_file, self.vote_list = BallotReader(config_filepath).read()
        self.show_display = show_display

    def run(self):
        """
        Runs all elections for all candidates to completion
        """
        file_output: list[str] = []

        for position_metadata in self.vote_list:
            election_runner = RankedChoiceRunner(
                position_metadata.ballots,
                candidates_running=position_metadata.num_candidates,
                candidates_required=position_metadata.num_winners,
                ballot_size=position_metadata.num_candidates,
                threshold=position_metadata.threshold,
            )

            if self.show_display:
                election_display = RankedChoiceDisplay(
                    election_runner,
                    title=position_metadata.name,
                )

                election_display.run_election_display()
            else:
                for run in election_runner.run_election():
                    _exhaust(run)

            file_output.append(f"Winners for {position_metadata.name} (candidates: {position_metadata.num_winners}; "
                               f"threshold: {position_metadata.threshold}):")

            file_output.extend(election_runner.winners)
            file_output.append("")

        with open(self.output_file, 'w') as output:
            output.write("\n".join(file_output))
