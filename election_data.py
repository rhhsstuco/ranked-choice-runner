from dataclasses import dataclass

from position_data import PositionData


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
    :param invalid_ballots: information about invalid ballots
    :param metadata: metadata about the election
    """
    position_data_list: list[PositionData]
    invalid_ballots: dict[str, int]
    metadata: ElectionMetadata
