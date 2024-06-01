import csv
import json
from collections import defaultdict, OrderedDict
from typing import Any, Tuple, List

from custom_types import Ballot
from position_data import PositionData


class BallotReader:
    """
    Reads the ballot information from a csv file using the config JSON file specified
    by the `metadata_filepath` parameter.
    """

    def __init__(self, metadata_filepath: str):
        """
        Creates a `BallotReader` instance for reading ballots

        :arg metadata_filepath: the path of the configuration JSON file
        """
        self.metadata_filepath = metadata_filepath

    def read(self) -> tuple[str, list[PositionData]]:
        """
        Creates a `BallotReader` instance for reading ballots

        :return: a list of `PositionData` instances representing the ballots and parameters of
        the election for a single position.
        """
        with open(self.metadata_filepath) as file:
            config_dict: dict[str, Any] = json.load(file)

        assert "source" in config_dict
        assert "positions" in config_dict
        assert "threshold" in config_dict
        assert "output" in config_dict

        source = config_dict["source"]

        # dictionary of all positions to their metadata (as a dictionary)
        positions_metadata: dict[str, dict[str, Any]] = config_dict["positions"]

        # dictionary of all positions to their ballots
        vote_list: dict[str, list[Ballot]] = defaultdict(list)

        with open(source) as file:
            reader = csv.reader(file, delimiter=",")

            # skip the headers
            next(reader, None)

            # Assign ballots to positions
            for i, row in enumerate(reader):
                start = 1

                for name, position_metadata in positions_metadata.items():
                    assert "num_candidates" in position_metadata
                    assert "num_winners" in position_metadata

                    num_candidates = position_metadata["num_candidates"]

                    if num_candidates <= 0:
                        raise ValueError(f"Invalid amount of choices ({num_candidates}) for position ({name}).")

                    if num_candidates <= 2:
                        vote_list[name].append(tuple(row[start:start + 1]))
                    else:
                        vote_list[name].append(tuple(row[start:(start + num_candidates)]))

                    start += num_candidates

        position_data_list: list[PositionData] = []

        global_threshold = float(config_dict["threshold"])

        for position, ballots in vote_list.items():
            # Reads the election threshold parameter, defaulting to the global value if needed
            if "threshold" in config_dict["positions"][position]:
                threshold = float(config_dict["positions"][position]["threshold"])
            else:
                threshold = global_threshold

            position_data_list.append(
                PositionData(
                    name=position,
                    ballots=vote_list[position],
                    num_candidates=config_dict["positions"][position]["num_candidates"],
                    num_winners=config_dict["positions"][position]["num_winners"],
                    threshold=threshold
                )
            )

        return str(config_dict["output"]), position_data_list
