from collections.abc import MutableMapping

Ballot = tuple[str, ...]
VoteDict = MutableMapping[str, list[Ballot]]
