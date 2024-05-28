import csv
from collections.abc import Mapping


class MetadataReader:
    def __init__(self, filepath: str):
        self.filepath = filepath

    def read(self) -> Mapping[str, str]:
        metadata_dict: dict[str, str] = {}

        with open(self.filepath) as file:
            reader = csv.reader(file, delimiter=",")

            # skip the headers
            next(reader, None)

            for row in reader:
                if len(row) > 2:
                    raise ValueError("Invalid file formatting")
                metadata_dict[row[0]] = row[1]

            return metadata_dict

