from dataclasses import dataclass

from custom_types import Ballot


@dataclass
class PositionMetadata:
    """
    A dataclass containing parameters about the election for a position

    :param name: the position name
    :param num_candidates: the number of total candidates running for the position
    :param num_winners: the number of candidates required for the position
    :param threshold: a flot
    """
    name: str
    num_candidates: int
    num_winners: int
    threshold: float
    ballots: list[Ballot]

    def __post_init__(self):
        """
        :raises:
            ValueError: if the argument 'threshold' is not between 0.0 and 1.0 (inclusive).
        """
        if not 0 <= self.threshold <= 1:
            raise ValueError("Argument 'threshold' must be between 0.0 and 1.0 (inclusive).")
