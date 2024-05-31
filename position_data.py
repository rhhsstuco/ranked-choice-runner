from dataclasses import dataclass

from custom_types import Ballot


@dataclass
class PositionData:
    name: str
    num_candidates: int
    num_winners: int
    threshold: float
    ballots: list[Ballot]
