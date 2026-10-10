# Username command

Python 3 and the standard library are sufficient. No installation is needed.

Run the public interface:

```sh
python3 username.py alice
python3 username.py -- '  Alice  '
python3 username.py --help
```

Success prints a JSON object on stdout; errors and usage go to stderr.
`--` lets a username beginning with `-` be supplied as the positional argument.

Run the existing tests from this directory:

```sh
python3 -B -m unittest -v
```

The CLI can be invoked by its absolute path while the current directory is a
separate writable temporary directory. It requires no files in that directory.
