from collections import defaultdict
from collections.abc import Set

from custom_types import Ballot, VoteDict


def _copy_vote_dict(votes: VoteDict) -> VoteDict:
    new_vote_dict: VoteDict = defaultdict(list)

    for candidate, ballots in votes.items():
        new_vote_dict[candidate] = ballots.copy()

    return new_vote_dict


def _select_removable_candidates(votes: VoteDict) -> Set[str]:
    min_votes = min([len(ballots) for _, ballots in votes.items()])

    eliminated_candidates = set()

    for candidate, ballots in votes.items():
        if len(ballots) == min_votes:
            eliminated_candidates.add(candidate)

    return eliminated_candidates


class RankedChoiceRunner:
    def __init__(self, data: list[Ballot], *, candidates_running, ballot_size, candidates_required=1, threshold=0.5):
        if not data:
            raise ValueError("Invalid or empty ballot list.")

        if candidates_required > len(data[0]):
            raise ValueError("Number of required candidates exceed number of available candidates. ")

        self.data = data
        self._majority = int(len(self.data) * threshold) + 1
        self.eliminated: set[str] = set()
        self._candidates_running = candidates_running
        self._ballot_size = ballot_size
        self._candidates_required = candidates_required
        self.winners: set[str] = set()

    @property
    def num_ballots(self):
        return len(self.data)

    @property
    def candidates_running(self):
        return self._candidates_running

    @property
    def candidates_required(self):
        return self._candidates_required

    @property
    def ballot_size(self):
        return self._ballot_size

    @property
    def majority(self):
        return self._majority

    def run_election(self):
        for _ in range(self._candidates_required):
            votes: VoteDict = defaultdict(list)

            for ballot in self.data:
                votes[ballot[0]].append(ballot)

            self.eliminated.clear()
            self._transfer_votes(votes, self.winners)

            for eliminated_candidate in self.winners:
                del votes[eliminated_candidate]

            yield self._runoff_generator(votes)

    def reset(self):
        self.eliminated = set()
        self.winners = set()

    def _runoff_generator(self, votes: VoteDict):
        yield _copy_vote_dict(votes)

        has_majority = [len(ballots) > self._majority for _, ballots in votes.items()]

        while not any(has_majority):
            eliminated_candidates = _select_removable_candidates(votes)

            # There is a tie
            if len(eliminated_candidates) == len(votes):
                break

            self._transfer_votes(votes, eliminated_candidates)

            for eliminated_candidate in eliminated_candidates:
                del votes[eliminated_candidate]

            has_majority = [len(ballots) > self._majority for _, ballots in votes.items()]

            yield _copy_vote_dict(votes)

        candidate_list = [(candidate, ballots) for candidate, ballots in votes.items()]
        max_ballots = max([len(ballots) for _, ballots in candidate_list])
        winner_list = [candidate for candidate, ballots in candidate_list if len(ballots) == max_ballots]

        num_winners = len(winner_list)

        if num_winners == 0:
            raise ValueError("No winners. TODO: maybe fix this if possible.")
        elif num_winners == 1:
            self.winners.add(winner_list[0])
        else:
            self.winners.add(self._run_tiebreaker(winner_list, votes))

    def _transfer_votes(self, votes: VoteDict, eliminated_candidates: Set[str]):
        self.eliminated.update(eliminated_candidates)

        for candidate in eliminated_candidates:
            transferred_ballots = votes[candidate]

            for ballot in transferred_ballots:
                for choice in ballot:
                    if choice not in self.eliminated:
                        votes[choice].append(ballot)
                        break

    def _run_tiebreaker(self, winner_list: list[str], votes: VoteDict):
        winner = self._run_first_tiebreaker(winner_list, votes)

        if winner is None:
            return self._run_second_tiebreaker(winner_list, self.data)
        else:
            return winner

    def _run_first_tiebreaker(self, winner_list: list[str], votes: VoteDict):
        tiebreaker_dict: defaultdict[str, int] = defaultdict(int)

        for winner in winner_list:
            ballots = votes[winner]

            for ballot in ballots:
                try:
                    winner_index = ballot.index(winner)
                except ValueError:
                    continue

                tiebreaker_dict[winner] += (self._ballot_size - winner_index)

        max_points = max([point for point in tiebreaker_dict.values()])
        point_winners = [candidate for candidate, points in tiebreaker_dict.items() if points == max_points]

        if len(point_winners) == 1:
            return point_winners[0]
        else:
            return None

    def _run_second_tiebreaker(self, winner_list: list[str], all_ballots: list[Ballot]):
        tiebreaker_dict: defaultdict[str, int] = defaultdict(int)

        for winner in winner_list:
            for ballot in all_ballots:
                try:
                    winner_index = ballot.index(winner)
                except ValueError:
                    continue

                tiebreaker_dict[winner] += (self._ballot_size - winner_index)

        max_points = max([point for point in tiebreaker_dict.values()])
        point_winners = [candidate for candidate, points in tiebreaker_dict.items() if points == max_points]

        if len(point_winners) == 1:
            return point_winners[0]
        else:
            print(tiebreaker_dict)
            raise RuntimeError("The point tiebreaker system determines multiple winners. Please consult the election "
                               "committee.")

