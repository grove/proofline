"""Print a nonempty username without changing its value."""

import argparse
import json


def main():
    parser = argparse.ArgumentParser(description="Print a username as JSON.")
    parser.add_argument("username")
    args = parser.parse_args()
    if not args.username:
        parser.error("username must not be empty or whitespace-only")
    print(json.dumps({"username": args.username}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
