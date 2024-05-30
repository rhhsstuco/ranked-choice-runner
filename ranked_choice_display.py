from custom_types import VoteDict

import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator
from ranked_choice_runner import RankedChoiceRunner


def _transform_votes(votes: VoteDict):
    candidates = list(votes.keys())
    ballots = [len(ballots) for ballots in votes.values()]

    return candidates, ballots


class RankedChoiceDisplay:
    def __init__(self, runner: RankedChoiceRunner, title: str, *, delay=1):
        self.runner = runner
        self.title = title
        self.delay = delay

    def run_election_display(self):
        for run in self.runner.run_election():
            initial_vote = next(run)

            candidates, ballot_counts = _transform_votes(initial_vote)

            fig, axes = plt.subplots()

            axes.yaxis.set_major_locator(MaxNLocator(integer=True))
            plt.title(self.title)
            plt.ylim([0, self.runner.num_ballots + 1])

            rects = plt.bar(
                candidates,
                ballot_counts,
                color="blue",
                align="center",
            )

            for rect, ballot_count in zip(rects, ballot_counts):
                if ballot_count > self.runner.majority:
                    rect.set_color("red")

            plt.pause(self.delay)

            for stage in run:
                candidates, ballot_counts = _transform_votes(stage)

                for rect in rects:
                    rect.set_height(0)

                for rect, ballot_count in zip(rects, ballot_counts):
                    rect.set_height(ballot_count)

                    if ballot_count > self.runner.majority:
                        rect.set_color("red")

                fig.canvas.draw()
                plt.pause(self.delay)
