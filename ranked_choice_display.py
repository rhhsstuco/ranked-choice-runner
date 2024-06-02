from collections import defaultdict

from matplotlib.axes import Axes
from matplotlib.backend_bases import Event
from matplotlib.container import BarContainer
from matplotlib.figure import Figure
from matplotlib.text import Text
from matplotlib.widgets import Button

from custom_types import VoteDict, Ballot

import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator
from ranked_choice_runner import RankedChoiceRunner


def _make_ordinal(n: int):
    """
    Convert an integer into its ordinal representation::

    make_ordinal(0)   => '0th'
    make_ordinal(3)   => '3rd'
    make_ordinal(122) => '122nd'
    make_ordinal(213) => '213th'
    """
    if 11 <= (n % 100) <= 13:
        suffix = 'th'
    else:
        suffix = ['th', 'st', 'nd', 'rd', 'th'][min(n % 10, 4)]
    return str(n) + suffix


def _transform_votes(votes: VoteDict):
    candidates = list(votes.keys())
    ballots = list(votes.values())
    ballots_counts = [len(ballots) for ballots in ballots]

    return candidates, ballots, ballots_counts


def _display_ballots(candidate: str, ballots: list[Ballot]):
    if len(ballots) == 0:
        return

    ballot_place_counts: defaultdict[int, int] = defaultdict(int)

    for ballot in ballots:
        try:
            idx = ballot.index(candidate)
        except ValueError:
            continue

        ballot_place_counts[idx + 1] += 1

    if len(ballot_place_counts) == 0:
        return

    subplots: tuple[Figure, Axes] = plt.subplots()
    fig, axes = subplots

    labels = []
    bars = []

    sorted_keys = sorted(ballot_place_counts.keys())
    sorted_values = [ballot_place_counts[key] for key in sorted_keys]
    ballots_psa = [sorted_values[0]]

    for i, key in enumerate(sorted_keys):
        if i == 0:
            continue

        ballots_psa.append(ballots_psa[i - 1] + sorted_values[i])

    axes.yaxis.set_major_locator(MaxNLocator(integer=True))
    plt.ylim([0, max(ballots_psa) * 1.2])
    plt.title(f"Vote Distribution for {candidate}")

    ballots_psa.reverse()

    for i, key in enumerate(reversed(sorted_keys)):
        labels.append(f"{_make_ordinal(key)} choice")

        bar = axes.bar(
            ["Vote Distribution"],
            ballots_psa[i],
            align="center",
        )

        bars.append(bar)

        prev_height = 0 if i == len(ballots_psa) - 1 else ballots_psa[i + 1]

        num_votes = ballots_psa[i] - prev_height
        text_height = ballots_psa[i]
        axes.text(bar[0].get_x() + bar[0].get_width() / 2., 1.05 * text_height,
                  str(num_votes),
                  ha='center', va='bottom')

    plt.legend(tuple(bars), tuple(labels))
    plt.show(block=False)

    return fig


class _ElectionDisplay:
    def __init__(self, *, stages: list[VoteDict], runner: RankedChoiceRunner, title: str):
        self.candidates = []
        self.ballots = []
        self.ballot_counts = []
        self.stages = stages
        self.index = 0
        self._runner = runner
        self.title = title
        self.textboxes = []
        self.distribution_figures = []

        self._init_election_display()

    def next(self):
        self.index += 1

        if self.index >= len(self.stages):
            self._close_distribution_figures()
            plt.close(self.fig)
            return

        votes = self.stages[self.index]

        self.candidates, self.ballots, self.ballot_counts = _transform_votes(votes)

        self.textboxes = self._update_graph(
            self.axes,
            self.textboxes,
            self.rects
        )

    def prev(self):
        self.index -= 1

        if self.index < 0:
            self.index = 0
            return

        votes = self.stages[self.index]

        self.candidates, self.ballots, self.ballot_counts = _transform_votes(votes)

        self.textboxes = self._update_graph(
            self.axes,
            self.textboxes,
            self.rects,
        )

    def _close_distribution_figures(self):
        for fig in self.distribution_figures:
            plt.close(fig)

    def _click_handler(self, e: Event):
        for candidate, ballots, rect in zip(self.candidates, self.ballots, self.rects):
            if rect.contains(e)[0]:
                fig = _display_ballots(candidate, ballots)

                self.distribution_figures.append(fig)

    def _update_graph(
            self,
            axes: Axes,
            prev_textboxes: list[Text],
            rects: BarContainer,
    ):
        self._close_distribution_figures()

        for textbox in prev_textboxes:
            textbox.remove()

        prev_textboxes.clear()

        for rect in rects:
            rect.set_height(0)

        self.axes.set_xticks(range(len(self.candidates)), self.candidates)

        for rect, ballot_count in zip(rects, self.ballot_counts):
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

        self.candidates, self.ballots, self.ballot_counts = _transform_votes(initial_vote)

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
            self.candidates,
            self.ballot_counts,
            color="blue",
            align="center",
        )

        self.fig.canvas.mpl_connect('button_press_event', lambda e: self._click_handler(e))

        self.textboxes = self._update_graph(
            self.axes,
            self.textboxes,
            self.rects,
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
