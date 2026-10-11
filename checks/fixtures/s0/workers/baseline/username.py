"""Print the supplied username as JSON."""

import argparse
import json


def main():
    parser = argparse.ArgumentParser(description="Print a username as JSON.")
    parser.add_argument("username")
    args = parser.parse_args()
    print(json.dumps({"username": args.username}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
