import json
import sys
import app


def main():
    if sys.argv[1:] == ["--version"]:
        print("api-v1")
        return 0
    if sys.argv[1:]:
        print("ERROR: unsupported arguments", file=sys.stderr)
        return 2
    try:
        value = app.process(json.load(sys.stdin))
        print(json.dumps(value, ensure_ascii=False, sort_keys=True))
        return 0
    except (ValueError, TypeError, NotImplementedError) as error:
        print("ERROR: " + str(error), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
