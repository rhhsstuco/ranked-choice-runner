import csv
import json
from collections import defaultdict, OrderedDict
from typing import Any

from custom_types import Ballot
from position_data import PositionData


class BallotReader:
    def __init__(self, metadata_filepath: str):
        self.metadata_filepath = metadata_filepath

    def read(self) -> list[PositionData]:
        with open(self.metadata_filepath) as file:
            metadata_dict: dict[str, Any] = json.load(file)

        assert "source" in metadata_dict
        assert "positions" in metadata_dict

        positions_metadata: dict[str, dict[str, Any]] = metadata_dict["positions"]

        vote_list: dict[str, list[Ballot]] = defaultdict(list)

        with open(metadata_dict["source"]) as file:
            reader = csv.reader(file, delimiter=",")

            # skip the headers
            next(reader, None)

            for i, row in enumerate(reader):

                start = 1

                for name, position_metadata in positions_metadata.items():
                    num_candidates = position_metadata["num_candidates"]

                    if num_candidates <= 0:
                        raise ValueError(f"Invalid amount of choices ({num_candidates}) for position ({name}).")

                    if num_candidates <= 2:
                        vote_list[name].append(tuple(row[start:start + 1]))
                    else:
                        vote_list[name].append(tuple(row[start:(start + num_candidates)]))

                    start += num_candidates

        position_data_list: list[PositionData] = []

        for position, ballots in vote_list.items():
            position_data_list.append(
                PositionData(
                    name=position,
                    ballots=vote_list[position],
                    num_candidates=metadata_dict["positions"][position]["num_candidates"],
                    num_winners=metadata_dict["positions"][position]["num_winners"]
                )
            )

        return position_data_list
