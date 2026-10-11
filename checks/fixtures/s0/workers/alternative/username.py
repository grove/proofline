"""Parse a valid username and write its original value as JSON."""

from argparse import ArgumentParser, ArgumentTypeError
from json import dumps
import sys


def nonblank(value):
    if all(character.isspace() for character in value):
        raise ArgumentTypeError("username must not be empty or whitespace-only")
    return value


def main():
    command = ArgumentParser(description="Print a username as JSON.")
    command.add_argument("username", type=nonblank)
    username = command.parse_args().username
    sys.stdout.write(dumps(dict(username=username)) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
