from collections.abc import MutableMapping
from typing import Annotated

Ballot = tuple[str, ...]
VoteDict = Annotated[
    MutableMapping[str, list[Ballot]],
    "A mutable mapping representing a vote distribution dictionary at a stage in an election."
    "The dictionary maps candidates to the specific ballots that count towards its vote total."
]

