import csv
import json
from collections import defaultdict
from dataclasses import dataclass
from typing import Any, Mapping

from custom_types import Ballot
from position_metadata import PositionData


@dataclass(frozen=True, kw_only=True)
class ElectionMetadata:
    """
    A dataclass containing parameters and metadata about the election.

    :param output_file: the path of the output file
    :param num_ballots: the total number of ballots cast
    :param show_display: if the election results and process should be displayed
    """
    output_file: str
    num_ballots: int
    show_display: bool


@dataclass(frozen=True, kw_only=True)
class ElectionData:
    """
    A dataclass containing parameters and metadata about the election.

    :param position_data_list: a list of election data per position
    :param metadata: metadata about the election
    """
    position_data_list: list[PositionData]
    metadata: ElectionMetadata


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

    def read(self):
        """
        Creates a ``BallotReader`` instance for reading ballots.

        :return: a tuple containing the output filepath, a list of ``PositionData`` instances representing the
        ballots and parameters of the election for a single position, and the total number of ballots
        """
        with open(self.config_filepath) as file:
            config_dict: dict[str, Any] = json.load(file)

        # Check for key existence
        _check_key_exists_in_config("source", config_dict, "source", self.config_filepath)
        _check_key_exists_in_config("output", config_dict, "output", self.config_filepath)
        _check_key_exists_in_config("threshold", config_dict, "threshold", self.config_filepath)
        _check_key_exists_in_config("show_display", config_dict, "show_display", self.config_filepath)
        _check_key_exists_in_config("positions", config_dict, "positions", self.config_filepath)

        source = config_dict["source"]

        # Mapping of all positions to their metadata (as a dictionary)
        positions_metadata: dict[str, dict[str, Any]] = config_dict["positions"]

        # Mapping of all positions to their ballots
        vote_list: dict[str, list[Ballot]] = defaultdict(list)

        num_ballots = 0

        with open(source) as file:
            reader = csv.reader(file, delimiter=",")

            # Skip the headers
            next(reader, None)

            # Assign ballots to positions
            for i, row in enumerate(reader):
                start = 1
                num_ballots += 1

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
        position_data_list: list[PositionData] = []

        global_threshold = float(config_dict["threshold"])
        show_display = bool(config_dict["show_display"])

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
                    candidates=config_dict["positions"][position]["candidates"],
                    num_winners=int(config_dict["positions"][position]["num_winners"]),
                    threshold=threshold
                )
            )

        return ElectionData(
            position_data_list=position_data_list,
            metadata=ElectionMetadata(
                output_file=str(config_dict["output"]),
                num_ballots=num_ballots,
                show_display=show_display,
            )
        )
