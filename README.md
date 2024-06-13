# Ranked Choice Election Runner

This program runs a series of ranked choice elections as specified by the
13th Edition of the Student Council Constitution. The program also
visually displays each stage of each instant runoff round.

## What is Ranked Choice Voting

Ranked choice voting is an alternative voting system where each voter ranks
the candidates from most to least preferred. First, the votes are counted
only using the first choice of each ballot. If no candidate fails to secure
a majority, **instant runoff occurs**: candidates with the lowest amount of
first choice votes are eliminated and their votes transferred to the second
choice of each voter's ballot. This is repeated over and over until a
candidate secures a majority.

For positions with multiple spots (e.g. Co-President), an election is run to
determine one winner. Another election is then run, where the winner's votes
are immediately transferred to the second choice of each ballot. The winner of
this second election is then the second winner. This is repeated over and over
until the required amount of candidates is selected.

## Configuring the Runner

The configuration of the runner is determined using a `config.json` file
located alongside the `main.py` file. The configuration files specifies
the path to the input and output file, and metadata about each position.
The configuration schema is as follows:

* `source`: `string`
  * The path to the input `.csv` file.
* `output`: `string`
  * The path to the output `.txt` file.
* `threshold`: `number`
  * a floating point value between 0 and 1 (inclusive) which determines
    the percentage of votes that defines the majority.
  * Let `N` be the total amount of votes and `n` be the `threshold` value. Then
    `majority = floor(N * n) + 1`.
* `positions`: `object`
  * An object mapping each position name to metadata about the position
    in the following schema:
  * `num_candidates`: `number`
    * The total number of candidates **running** for this position.
  * `num_winners`: `number`
    * The total number of candidates **required** for this position.
  * `[threshold]`: `number (optional)`
    * An individualized threshold value (See `threshold` above) which applies
      only for the position which specifies it.
    * If this value is not given, it defaults to the `threshold` value specified above

An example of the schema is given below:

```json5
{
  "source": "_data.csv",
  "output": "results.txt",
  "threshold": 0.5,
  "positions": {
    "President": {
      "num_candidates": 4,
      "num_winners": 2
    },
    "Vice President": {
      "num_candidates": 2,
      "num_winners": 1
    },
    "Secretary": {
      "num_candidates": 3,
      "num_winners": 1,
      "threshold": 0.4,
    }
  }
}
```

## Input Format

The format of the input CSV file is designed to mimic that of Google Forms.
As such, the format goes as (the header values do not matter):

| Timestamp | Position A (1) | Position A (2) | ... | Position A (n) | Position B (1) | Position B (2) | ... | Position B (n) | ... |
|-----------|----------------|----------------|-----|----------------|----------------|----------------|-----|----------------|-----|
| timestamp | Choice 1 for A | Choice 2 for A | ... | Choice n for A | Choice 1 for B | Choice 2 for B | ... | Choice n for B | ... |
| timestamp | Choice 1 for A | Choice 2 for A | ... | Choice n for A | Choice 1 for B | Choice 3 for B | ... | Choice n for B | ... |
| ...       | ...            | ...            | ... | ...            | ...            | ...            | ... | ...            | ... |
