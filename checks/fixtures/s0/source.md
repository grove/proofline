# Original source — username validation

Improve the existing local Python username command without changing its public
interface or adding dependencies.

1. Reject an empty username and a username consisting entirely of whitespace,
   including tabs, line breaks, and Unicode whitespace. Use exit status `2`,
   write no success output to stdout, and include the clear error text
   `username must not be empty or whitespace-only` on stderr. Usage context may
   surround that text.
2. For every nonblank username that can be passed as a command-line argument,
   keep its exact value. In particular, do not trim, normalize, change case, or
   reject a name merely because it contains surrounding or internal whitespace.
   Continue to exit `0` and print one JSON object with exactly the `username`
   field holding the supplied string. Write no error to stderr.
3. Preserve the existing one-positional-argument interface, `--` argument
   terminator, successful `-h`/`--help`, and exit status `2` with a usage error for
   a missing or extra positional argument. Do not add file or network effects.

Whitespace here includes the characters classified as whitespace by Python 3
`str.isspace()`. That defines input behavior, not a required implementation.
JSON formatting and implementation structure are free choices. The command is
run with Python 3 using only the standard library.
