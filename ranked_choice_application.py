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

    def __init__(self, *, config_filepath: str):
        """
        :param config_filepath: the filepath to the config JSON file.
        """
        election_data = BallotReader(config_filepath).read()

        self.output_file = election_data.metadata.output_file
        self.num_ballots = election_data.metadata.num_ballots
        self.show_display = election_data.metadata.show_display
        self.vote_list = election_data.position_data_list
        self.invalid_ballots = election_data.invalid_ballots

    def run(self):
        """
        Runs all elections for all candidates to completion
        """

        file_output: list[str] = [
            f"Total Ballots: {self.num_ballots}",
            "",
        ]

        if self.invalid_ballots is not None:
            invalid_ballots_count = sum(self.invalid_ballots.values())

            file_output.append(
                f"Invalid Ballots: {invalid_ballots_count}",
            )

            for key, value in self.invalid_ballots.items():
                file_output.append(f"\t{key}: {value}")

            file_output.append("")

        for position_metadata in self.vote_list:
            election_runner = RankedChoiceRunner(
                position_metadata.ballots,
                candidates=position_metadata.candidates,
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
                               f"threshold: {position_metadata.threshold},"
                               f"number of ballots: {len(position_metadata.ballots)}):")

            for winner in election_runner.winners:
                if winner in election_runner.notes:
                    file_output.append(f"{winner} ({', '.join(election_runner.notes[winner])})")
                else:
                    file_output.append(winner)

            file_output.append("")

        with open(self.output_file, 'w') as output:
            output.write("\n".join(file_output))
