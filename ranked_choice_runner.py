from collections import defaultdict
from collections.abc import Set, Mapping, MutableMapping
from typing import Callable, Literal

from custom_types import Ballot, VoteDict
from utils import make_ordinal


def _copy_vote_dict(votes: VoteDict) -> VoteDict:
    """
    Performs a shallow copy of a ``VoteDict``, where the contained ballots retain their object identity.

    :param votes: the ``VoteDict`` to copy
    :return: a new shallow copy of the ``VoteDict``
    """
    new_vote_dict: VoteDict = defaultdict(list)

    for candidate, ballots in votes.items():
        new_vote_dict[candidate] = ballots.copy()

    return new_vote_dict


def _select_removable_candidates(votes: VoteDict) -> Set[str]:
    """
    Selects a set of the candidates which are eliminated via instant runoff (they have the lowest number of votes).

    :param votes: the VoteDict from which to compute the removable candidates
    :return: a set of candidates which are to be eliminated from the runoff
    """
    min_votes = min([len(ballots) for _, ballots in votes.items()])

    eliminated_candidates = set()

    for candidate, ballots in votes.items():
        if len(ballots) == min_votes:
            eliminated_candidates.add(candidate)

    return eliminated_candidates


def _compute_tiebreaker_winner(tiebreaker_dict: Mapping[str, int]):
    """
    Helper method which computes the winner of a point-system tiebreaker

    :param tiebreaker_dict: a mapping of candidates to points
    :return: the winning candidate or ``None`` if no winner can be determined
    """
    max_points = max([point for point in tiebreaker_dict.values()])
    point_winners = [candidate for candidate, points in tiebreaker_dict.items() if points == max_points]

    if len(point_winners) == 1:
        return point_winners[0]
    else:
        return None


class RankedChoiceRunner:
    """
    Runs a ranked choice election for a single position.
    """

    def __init__(self,
                 data: list[Ballot],
                 *,
                 candidates: list[str],
                 ballot_size: int,
                 candidates_required: int = 1,
                 threshold: float = 0.5
                 ):
        """
        :param data: a list of all ballots in the election, as a list of tuples of strings.
        :param candidates: the list of candidates running in the election.
        :param ballot_size: the size of each ballot.
        :param candidates_required: the number of candidates required for the elected position.
        :param threshold: the percentage of votes that defines the majority.

        :raises:
            ValueError if ``data`` is invalid or empty.
            ValueError if ``required_candidates`` > ``candidates_running``
        """
        if not data:
            raise ValueError("Invalid or empty ballot list.")

        if candidates_required > len(candidates):
            raise ValueError("Number of required candidates exceed number of available candidates. ")

        self._data = data
        self._majority = int(len(self._data) * threshold) + 1
        self._eliminated: set[str] = set()
        self._candidates = candidates
        self._candidates_running = len(candidates)
        self._ballot_size = ballot_size
        self._candidates_required = candidates_required
        self.winners: set[str] = set()
        self.notes: MutableMapping = defaultdict(list)

    @property
    def num_ballots(self):
        """
        :return: The total number of ballots in the election.
        """
        return len(self._data)

    @property
    def candidates_running(self):
        """
        :return: The total number of candidates running in the election.
        """
        return self._candidates_running

    @property
    def candidates_required(self):
        """
        :return: The total number of candidates required in the election.
        """
        return self._candidates_required

    @property
    def ballot_size(self):
        """
        :return: The size of a ballot in the election
        """
        return self._ballot_size

    @property
    def majority(self):
        """
        :return: The amount of votes required to gain a majority
        """
        return self._majority

    def run_election(self):
        """
        Runs the election.

        :return: a generator which generates generators which generates a ballot distribution dictionary (``VoteDict``)
                 for each stage in the election.
        """
        for _ in range(self._candidates_required):
            votes: VoteDict = {}

            for candidate in self._candidates:
                votes[candidate] = []

            # Construct initial ballot distribution dictionary (VoteDict)
            for ballot in self._data:
                votes[ballot[0]].append(ballot)

            # Redistribute votes that belong to already-decided winners
            self._eliminated.clear()
            self._transfer_votes(votes, self.winners)

            for eliminated_candidate in self.winners:
                del votes[eliminated_candidate]

            yield self._runoff_generator(votes)

    def reset(self):
        """
        Resets the election to be run again.
        """
        self._eliminated = set()
        self.winners = set()

    def _runoff_generator(self, votes: VoteDict):
        """
        Performs instant runoff, and generates a vote distribution dictionary (``VoteDict``) for
        each distinct stage of the runoff.

        :param votes: the initial vote distribution dictionary (``VoteDict``).
        :return: a generator which generates VoteDicts for each stage of the election.
        """
        yield _copy_vote_dict(votes)

        has_majority = [len(ballots) > self._majority for _, ballots in votes.items()]

        while not any(has_majority):
            eliminated_candidates = _select_removable_candidates(votes)

            # There is a tie
            if len(eliminated_candidates) == len(votes):
                break

            # Transfer votes from eliminated candidates and delete
            self._transfer_votes(votes, eliminated_candidates)

            for eliminated_candidate in eliminated_candidates:
                del votes[eliminated_candidate]

            has_majority = [len(ballots) > self._majority for _, ballots in votes.items()]

            yield _copy_vote_dict(votes)

        # Compile list of winners
        candidate_list = [(candidate, ballots) for candidate, ballots in votes.items()]
        max_ballots = max([len(ballots) for _, ballots in candidate_list])
        winner_list = [candidate for candidate, ballots in candidate_list if len(ballots) == max_ballots]

        num_winners = len(winner_list)

        if num_winners == 0:
            raise ValueError("No winners. This shouldn't be possible")
        elif num_winners == 1:
            self.winners.add(winner_list[0])
        else:
            try:
                winner, tiebreaker_iteration = self._run_tiebreaker(winner_list, votes)
                self.notes[winner].append(f"determined by the {make_ordinal(tiebreaker_iteration)} tiebreaker")
                self.winners.add(winner)
            except RuntimeError:
                self.winners.add(f"A tie has occurred between {', '.join(winner_list)}")

    def _transfer_votes(self, votes: VoteDict, eliminated_candidates: Set[str]):
        """
        Transfer votes from the candidates in ``eliminated_candidates`` to others as specified by their ranked ballot.

        :param votes: the vote distribution dictionary (``VoteDict``) on which to operate .
        :param eliminated_candidates: the set of candidates to be eliminated.
        """
        self._eliminated.update(eliminated_candidates)

        for candidate in eliminated_candidates:
            transferred_ballots = votes[candidate]

            for ballot in transferred_ballots:
                for choice in ballot:
                    # Transfer ballot to first non-eliminated candidate
                    if choice not in self._eliminated:
                        votes[choice].append(ballot)
                        break

    def _run_tiebreaker(self,
                        winner_list: list[str],
                        votes: VoteDict, *,
                        on_tie: Callable[[list[str]], None] | None = None
                        ) -> tuple[str, Literal[1, 2]]:
        """
        Runs the tiebreaker procedure in the case that multiple candidates are tied.

        :param winner_list: the list of potential winning candidates.
        :param votes: the current vote distribution dictionary (``VoteDict``) of the election.
        :param on_tie: a consumer function to be called with the list of tied winners .
        :return: the singular winner.
        :raises:
            ValueError: if the tiebreaker system still determines a tie.
        """
        winner = self._run_first_tiebreaker(winner_list, votes)

        if winner is None:
            winner = self._run_second_tiebreaker(winner_list, self._data)

            if winner is None:
                if on_tie is not None:
                    on_tie(winner_list)

                raise RuntimeError("The point tiebreaker system determines multiple winners. Please consult the "
                                   "election committee.")
            else:
                tiebreaker: Literal[1, 2] = 2
        else:
            tiebreaker: Literal[1, 2]  = 1

        return winner, tiebreaker

    def _run_first_tiebreaker(self, winner_list: list[str], votes: VoteDict):
        """
        Runs the first tiebreaker. **All votes belonging to each of the potential winning candidates** are
        reduced to a numerical point total where a first choice vote is worth ``N`` points, where ``N`` is the
        amount of candidates, a second choice vote is worth ``(N-1)`` votes, and so on and so forth.

        :param winner_list: a list of the potential winning candidates.
        :param votes: the current vote distribution dictionary (``VoteDict``) of the election.
        :return: the singular winner or ``None`` if no singular winner can be determined.
        """
        tiebreaker_dict: defaultdict[str, int] = defaultdict(int)

        for winner in winner_list:
            ballots = votes[winner]

            for ballot in ballots:
                try:
                    winner_index = ballot.index(winner)
                except ValueError:
                    continue

                tiebreaker_dict[winner] += (self._ballot_size - winner_index)

        return _compute_tiebreaker_winner(tiebreaker_dict)

    def _run_second_tiebreaker(self, winner_list: list[str], all_ballots: list[Ballot]):
        """
        Runs the second tiebreaker. **All votes cast in the election** are
        reduced to a numerical point total where a first choice vote is worth ``N`` points, where ``N`` is the
        amount of candidates, a second choice vote is worth ``(N-1)`` votes, and so on and so forth.

        :param winner_list: a list of the potential winning candidates.
        :param all_ballots: all ballots cast in the election.
        :return: the singular winner or ``None`` if no singular winner can be distinguished.
        """
        tiebreaker_dict: defaultdict[str, int] = defaultdict(int)

        for winner in winner_list:
            for ballot in all_ballots:
                try:
                    winner_index = ballot.index(winner)
                except ValueError:
                    continue

                tiebreaker_dict[winner] += (self._ballot_size - winner_index)

        return _compute_tiebreaker_winner(tiebreaker_dict)
