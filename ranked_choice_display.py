from collections import defaultdict

from matplotlib.axes import Axes
from matplotlib.backend_bases import Event
from matplotlib.figure import Figure
from matplotlib.widgets import Button

from custom_types import VoteDict, Ballot

import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator
from ranked_choice_runner import RankedChoiceRunner

_TEXT_OFFSET = 20
_ORDINAL_SUFFIX_LIST = ['th', 'st', 'nd', 'rd', 'th']


def _make_ordinal(n: int):
    """
    Convert an integer into its ordinal representation.

    make_ordinal(0)   => '0th'
    make_ordinal(3)   => '3rd'
    make_ordinal(122) => '122nd'
    make_ordinal(213) => '213th'

    :param n: the integer to convert.
    :return: the ordinal representation of ``n``.
    """
    if 11 <= (n % 100) <= 13:
        suffix = 'th'
    else:
        suffix = _ORDINAL_SUFFIX_LIST[min(n % 10, 4)]

    return str(n) + suffix


def _transform_votes(votes: VoteDict):
    """
    Transform a ``MutableMapping[str, list[Ballot]]`` into 3 separate lists
    representing candidate names, ballot lists, and ballot counts.

    :arg votes the ``VoteDict`` to transform.
    :return three lists in a tuple representing the candidates, ballots, and ballot counts.
    """
    candidates = list(votes.keys())
    ballots = list(votes.values())
    ballots_counts = [len(ballots) for ballots in ballots]

    return candidates, ballots, ballots_counts


def _display_ballots(candidate: str, ballots: list[Ballot]):
    """
    Displays the vote distribution (1st, 2nd, 3rd, ...) on a bar chart using matplotlib.

    :arg candidate the candidate whose votes are displayed.
    :arg ballots the ballots for the candidate.
    """
    if len(ballots) == 0:
        return

    # Maps the vote rank to the amount of votes
    ballot_place_counts: defaultdict[int, int] = defaultdict(int)

    for ballot in ballots:
        try:
            idx = ballot.index(candidate)
        except ValueError:
            continue

        ballot_place_counts[idx + 1] += 1

    # No valid ballots
    if len(ballot_place_counts) == 0:
        return

    subplots: tuple[Figure, Axes] = plt.subplots()
    fig, axes = subplots

    labels = []
    bars = []

    # Creates a Prefix Sum Array where the value at each index i
    # is the sum of the votes ranked higher than or equal to i + 1.
    # E.g. index 2 is the sum of the first and second ranked votes
    sorted_keys = sorted(ballot_place_counts.keys())
    sorted_values = [ballot_place_counts[key] for key in sorted_keys]
    ballots_psa = [sorted_values[0]]

    for i, key in enumerate(sorted_keys):
        if i == 0:
            continue

        ballots_psa.append(ballots_psa[i - 1] + sorted_values[i])

    # Plot metadata
    axes.yaxis.set_major_locator(MaxNLocator(integer=True))
    plt.ylim([0, max(ballots_psa) * 1.2])
    plt.title(f"Vote Distribution for {candidate}")

    ballots_psa.reverse()

    # Construct bars
    for i, key in enumerate(reversed(sorted_keys)):
        labels.append(f"{_make_ordinal(key)} choice")

        # Create bar
        bar = axes.bar(
            ["Vote Distribution"],
            ballots_psa[i],
            align="center",
        )

        bars.append(bar)

        prev_height = 0 if i == len(ballots_psa) - 1 else ballots_psa[i + 1]

        # Computes label value and location
        num_votes = ballots_psa[i] - prev_height
        text_height = ballots_psa[i]
        axes.text(bar[0].get_x() + bar[0].get_width() / 2., text_height + _TEXT_OFFSET,
                  str(num_votes),
                  ha='center', va='bottom')

    plt.legend(tuple(bars), tuple(labels))
    plt.show(block=False)

    return fig


class _ElectionDisplay:
    """
    Helper class that displays the stages of one election run (where one candidate is elected).
    """

    def __init__(self, *, stages: list[VoteDict], runner: RankedChoiceRunner, title: str):
        """
        :param stages: the state of the ballot distribution at each point in the election.
        :param runner: the runner responsible for running the election. Contains useful election metadata.
        :param title: the title of the displayed matplotlib chart.
        """
        self.stages = stages
        self._runner = runner
        self.title = title
        self.index = 0

        self.candidates = []
        self.ballots = []
        self.ballot_counts = []
        self.textboxes = []
        self.distribution_figures = []

        self._init_election_display()

    def _next(self):
        """
        Moves the displayed chart to the next stage of the election,
        closing the chart window if the end is reached.
        """
        # Closes the chart window
        if self.index >= len(self.stages) - 1:
            self._close_distribution_figures()
            plt.close(self.fig)
            return

        self.index += 1

        votes = self.stages[self.index]
        self.candidates, self.ballots, self.ballot_counts = _transform_votes(votes)

        self._update_graph()

    def _prev(self):
        """
        Moves the displayed chart to the next stage of the election,
        closing the chart window if the end is reached.
        """
        if self.index <= 0:
            return

        self.index -= 1

        votes = self.stages[self.index]
        self.candidates, self.ballots, self.ballot_counts = _transform_votes(votes)

        self._update_graph()

    def _close_distribution_figures(self):
        """
        Closes the figures displaying vote distributions for candidates.
        """
        for fig in self.distribution_figures:
            plt.close(fig)

    def _bar_click_handler(self, e: Event):
        """
        Handles the click event which occurs on the bars on the bar graph.

        :param e the event object, containing event metadata.
        """
        for candidate, ballots, rect in zip(self.candidates, self.ballots, self.rects):
            if rect.contains(e)[0]:
                fig = _display_ballots(candidate, ballots)

                self.distribution_figures.append(fig)

    def _update_graph(self):
        """
        Updates the vote chart display.
        """
        # Resetting graph
        self._close_distribution_figures()

        for textbox in self.textboxes:
            textbox.remove()

        self.textboxes.clear()

        for rect in self.rects:
            rect.set_height(0)

        # Sets ticks
        self.axes.set_xticks(range(len(self.candidates)), self.candidates)

        # Sets the rectangles to the appropriate height
        for rect, ballot_count in zip(self.rects, self.ballot_counts):
            rect.set_height(ballot_count)

            # Changes color if a majority is attained
            if ballot_count > self._runner.majority:
                rect.set_color("red")
            else:
                rect.set_color("blue")

            height = rect.get_height()
            textbox = self.axes.text(rect.get_x() + rect.get_width() / 2., height + _TEXT_OFFSET,
                                     str(ballot_count),
                                     ha='center', va='bottom')

            self.textboxes.append(textbox)

        # Redraw
        self.fig.canvas.draw()
        plt.pause(0.02)

    def _init_election_display(self):
        """
        Initialized the vote chart display by drawing the initial stage and setting up event listeners.
        """
        initial_vote = self.stages[0]

        self.candidates, self.ballots, self.ballot_counts = _transform_votes(initial_vote)

        subplots: tuple[Figure, Axes] = plt.subplots()
        self.fig, self.axes = subplots

        # Sets graph metadata
        # Sets the y-axis markers to integers only
        self.axes.yaxis.set_major_locator(MaxNLocator(integer=True))
        plt.title(self.title)
        plt.ylim([0, self._runner.num_ballots + 1])

        # Allocate space for 'next' and 'prev' buttons
        self.fig.subplots_adjust(bottom=0.2)
        ax_prev = self.fig.add_axes((0.7, 0.05, 0.1, 0.075))
        ax_next = self.fig.add_axes((0.81, 0.05, 0.1, 0.075))

        # Create buttons and attached event listeners
        next_button = Button(ax_next, 'Next')
        next_button.on_clicked(lambda e: self._next())
        prev_button = Button(ax_prev, 'Prev')
        prev_button.on_clicked(lambda e: self._prev())

        # Constructs initial bar chart
        self.rects = self.axes.bar(
            self.candidates,
            self.ballot_counts,
            color="blue",
            align="center",
        )

        # Attach listener to graph itself to display vote distributions
        self.fig.canvas.mpl_connect('button_press_event', lambda e: self._bar_click_handler(e))

        self._update_graph()

        plt.pause(0.5)
        plt.show(block=True)


class RankedChoiceDisplay:
    """
    Displays a full election cycle for one position.
    This includes instant runoffs and multiple windows for multiple candidates.
    """

    def __init__(self, runner: RankedChoiceRunner, title: str):
        """
        :param runner: the object responsible for running the elections to completion.
        :param title: the title displayed by each window (e.g. position name).
        """
        self.runner = runner
        self.title = title

    def run_election_display(self):
        """
        Runs the election to completion and displays the stages of each election.
        """
        for run in self.runner.run_election():
            _ElectionDisplay(stages=list(run), runner=self.runner, title=self.title)
