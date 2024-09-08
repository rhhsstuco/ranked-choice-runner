import csv
import json
from collections import defaultdict
from typing import Any, Mapping

from custom_types import Ballot
from position_metadata import PositionMetadata


def _check_key_exists_in_config(key: str, mapping: Mapping, key_path: str, config_filepath: str):
    """
    Helper method which checks for the existence of a key in a config mapping
    and displays a user-friendly error message if it does not.

    :param key: the key whose existence to verify.
    :param mapping: the mapping that may or may not contain the key.
    :param key_path: the path to the key within the JSON config file (should be in dot notation).
    :param config_filepath: the filepath to the configuration JSON file.
    :raises:
        ValueError: if the key does not exist within the mapping.
    """
    if key not in mapping:
        raise ValueError(f"Key '{key_path}' does not exist within {config_filepath}")


class BallotReader:
    """
    Reads the ballot information from a csv file using the config JSON file specified
    by the ``config_filepath`` parameter.
    """

    def __init__(self, config_filepath: str):
        """
        :param config_filepath: the path of the configuration JSON file
        """
        self.config_filepath = config_filepath

    def read(self) -> tuple[str, list[PositionMetadata]]:
        """
        Creates a ``BallotReader`` instance for reading ballots.

        :return: a tuple containing the output filepath and a list of ``PositionData`` instances representing the
        ballots and parameters of the election for a single position.
        """
        with open(self.config_filepath) as file:
            config_dict: dict[str, Any] = json.load(file)

        # Check for key existence
        _check_key_exists_in_config("source", config_dict, "source", self.config_filepath)
        _check_key_exists_in_config("output", config_dict, "output", self.config_filepath)
        _check_key_exists_in_config("threshold", config_dict, "threshold", self.config_filepath)
        _check_key_exists_in_config("positions", config_dict, "positions", self.config_filepath)

        source = config_dict["source"]

        # Mapping of all positions to their metadata (as a dictionary)
        positions_metadata: dict[str, dict[str, Any]] = config_dict["positions"]

        # Mapping of all positions to their ballots
        vote_list: dict[str, list[Ballot]] = defaultdict(list)

        with open(source) as file:
            reader = csv.reader(file, delimiter=",")

            # Skip the headers
            next(reader, None)

            # Assign ballots to positions
            for i, row in enumerate(reader):
                start = 1

                for name, position_metadata in positions_metadata.items():
                    _check_key_exists_in_config(
                        "candidates",
                        position_metadata,
                        f"position.{name}.candidates",
                        self.config_filepath
                    )
                    _check_key_exists_in_config(
                        "num_winners",
                        position_metadata,
                        f"position.{name}.num_winners",
                        self.config_filepath
                    )

                    candidates = position_metadata["candidates"]
                    num_candidates = len(candidates)

                    if num_candidates <= 0:
                        raise ValueError(f"Invalid amount of choices ({num_candidates}) for position ({name}).")

                    ballot = tuple(row[start:(start + num_candidates)])

                    if not all(ballot):
                        start += num_candidates
                        continue

                    vote_list[name].append(ballot)

                    start += num_candidates

        # List of position metadata
        position_metadata_list: list[PositionMetadata] = []

        global_threshold = float(config_dict["threshold"])

        for position, ballots in vote_list.items():
            # Reads the election threshold parameter, defaulting to the global value if needed
            if "threshold" in config_dict["positions"][position]:
                threshold = float(config_dict["positions"][position]["threshold"])
            else:
                threshold = global_threshold

            position_metadata_list.append(
                PositionMetadata(
                    name=position,
                    ballots=vote_list[position],
                    candidates=config_dict["positions"][position]["candidates"],
                    num_winners=config_dict["positions"][position]["num_winners"],
                    threshold=threshold
                )
            )

        return str(config_dict["output"]), position_metadata_list
