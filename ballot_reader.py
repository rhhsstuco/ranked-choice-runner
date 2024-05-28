import csv

from custom_types import Ballot


class BallotReader:
    def __init__(self, filepath: str):
        self.filepath = filepath

    def read(self) -> list[Ballot]:
        with open(self.filepath) as file:
            reader = csv.reader(file, delimiter=",")

            # skip the headers
            next(reader, None)

            ballots = [tuple(row) for row in reader]
            return ballots

