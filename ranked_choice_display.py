from matplotlib.axes import Axes
from matplotlib.container import BarContainer
from matplotlib.figure import Figure
from matplotlib.text import Text
from matplotlib.widgets import Button

from custom_types import VoteDict

import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator
from ranked_choice_runner import RankedChoiceRunner


def _transform_votes(votes: VoteDict):
    candidates = list(votes.keys())
    ballots = [len(ballots) for ballots in votes.values()]

    return candidates, ballots


class _ElectionDisplay:
    def __init__(self, *, stages: list[VoteDict], runner: RankedChoiceRunner, title: str):
        self.stages = stages
        self.index = 0
        self._runner = runner
        self.title = title
        self.textboxes = []

        self._init_election_display()

    def next(self):
        self.index += 1

        if self.index >= len(self.stages):
            plt.close(self.fig)
            return

        votes = self.stages[self.index]

        candidates, ballot_counts = _transform_votes(votes)

        self.textboxes = self._update_graph(
            self.axes,
            self.textboxes,
            self.rects,
            candidates,
            ballot_counts
        )

    def prev(self):
        self.index -= 1

        if self.index < 0:
            self.index = 0
            return

        votes = self.stages[self.index]

        candidates, ballot_counts = _transform_votes(votes)

        self.textboxes = self._update_graph(
            self.axes,
            self.textboxes,
            self.rects,
            candidates,
            ballot_counts
        )

    def _update_graph(
            self,
            axes: Axes,
            prev_textboxes: list[Text],
            rects: BarContainer,
            candidates: list[str],
            ballot_counts: list[int]
    ):
        for textbox in prev_textboxes:
            textbox.remove()

        prev_textboxes.clear()

        for rect in rects:
            rect.set_height(0)

        self.axes.set_xticks(range(len(candidates)), candidates)

        for rect, ballot_count in zip(rects, ballot_counts):
            rect.set_height(ballot_count)

            if ballot_count > self._runner.majority:
                rect.set_color("red")
            else:
                rect.set_color("blue")

            height = rect.get_height()
            textbox = axes.text(rect.get_x() + rect.get_width() / 2., 1.05 * height,
                                str(ballot_count),
                                ha='center', va='bottom')

            prev_textboxes.append(textbox)

        # Redraw
        self.fig.canvas.draw()
        plt.pause(0.02)

        return prev_textboxes

    def _init_election_display(self):
        initial_vote = self.stages[0]

        candidates, ballot_counts = _transform_votes(initial_vote)

        subplots: tuple[Figure, Axes] = plt.subplots()
        self.fig, self.axes = subplots

        self.axes.yaxis.set_major_locator(MaxNLocator(integer=True))
        plt.title(self.title)
        plt.ylim([0, self._runner.num_ballots + 1])

        self.fig.subplots_adjust(bottom=0.2)
        ax_prev = self.fig.add_axes((0.7, 0.05, 0.1, 0.075))
        ax_next = self.fig.add_axes((0.81, 0.05, 0.1, 0.075))

        next_button = Button(ax_next, 'Next')
        next_button.on_clicked(lambda e: self.next())
        prev_button = Button(ax_prev, 'Prev')
        prev_button.on_clicked(lambda e: self.prev())

        self.rects = self.axes.bar(
            candidates,
            ballot_counts,
            color="blue",
            align="center",
        )

        self.textboxes = self._update_graph(
            self.axes,
            self.textboxes,
            self.rects,
            candidates,
            ballot_counts,
        )

        plt.pause(0.5)
        plt.show(block=True)


class RankedChoiceDisplay:
    def __init__(self, runner: RankedChoiceRunner, title: str, *, delay=1):
        self.runner = runner
        self.title = title

    def _update_graph(
            self,
            axes: Axes,
            prev_textboxes: list[Text],
            rects: BarContainer,
            ballot_counts: list[int]
    ):
        for textbox in prev_textboxes:
            textbox.remove()

        prev_textboxes.clear()

        for rect in rects:
            rect.set_height(0)

        for rect, ballot_count in zip(rects, ballot_counts):
            rect.set_height(ballot_count)

            if ballot_count > self.runner.majority:
                rect.set_color("red")

            height = rect.get_height()
            textbox = axes.text(rect.get_x() + rect.get_width() / 2., 1.05 * height,
                                str(ballot_count),
                                ha='center', va='bottom')

            prev_textboxes.append(textbox)

        return prev_textboxes

    def run_election_display(self):
        for run in self.runner.run_election():
            _ElectionDisplay(stages=list(run), runner=self.runner, title=self.title)
