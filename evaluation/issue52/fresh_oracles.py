"""Draft public-behavior probes, withheld from workers; independent review pending.

These accept different wrapping layouts. They do not grade documentation, all
source obligations, or interfaces that the source request leaves unspecified.
"""
import json


OPTIONS = ['--enable-verbose-logging', '--output-file-path', '--max-retry-count',
           '--disable-cache-mode', '--config-file-location', '--user-auth-token',
           '--auto-update-interval', '--force-overwrite-existing',
           '--network-timeout-seconds', '--debug-trace-enabled']


def usage_tokens():
    import click
    from click.testing import CliRunner

    for width in (None, 50, 65):
        for prog in ('program', 'a_program_name_that_is_deliberately_longer_than_the_entire_usage_line'):
            formatter = click.HelpFormatter(width=width)
            formatter.write_usage(prog, ' '.join(OPTIONS))
            text = click.unstyle(formatter.getvalue())
            # Only whitespace/layout is unconstrained: tokens and order must survive.
            assert text.split()[2:] == OPTIONS, (width, prog, text)

    @click.command()
    @click.argument('value', metavar='some-hyphenated-argument')
    def cli(value):
        raise AssertionError('Help must not execute the command')

    result = CliRunner().invoke(cli, ['--help'], terminal_width=50)
    assert result.exit_code == 0, result.output
    assert 'some-hyphenated-argument' in result.output
    formatter = click.HelpFormatter(width=65)
    formatter.write_usage('program', '')
    assert formatter.getvalue().strip() == 'Usage: program'


def usage_metadata():
    import click

    @click.group()
    def root():
        raise AssertionError('Inspection must not execute callbacks')

    @root.group()
    def sub():
        pass

    @sub.command()
    @click.argument('filename')
    def leaf(filename):
        pass

    def compare(row, ctx):
        # Source says get_usage output; the workaround strips its heading.
        actual = row.get('usage')
        assert isinstance(actual, str), row
        expected = ctx.get_usage()
        assert actual.split() in (expected.split(), expected.removeprefix('Usage: ').split())

    with click.Context(root, info_name='tool') as ctx:
        info = ctx.to_info_dict()
        compare(info.get('usage') and info or info['command'], ctx)
        with click.Context(sub, info_name='sub', parent=ctx) as subctx:
            compare(info['command']['commands']['sub'], subctx)
            with click.Context(leaf, info_name='leaf', parent=subctx) as leafctx:
                compare(info['command']['commands']['sub']['commands']['leaf'], leafctx)
    assert info['command']['name'] == 'root'
    assert info['command']['commands']['sub']['commands']['leaf']['params']
    json.dumps(info)


CASES = {'click-usage-hyphens': usage_tokens, 'click-usage-metadata': usage_metadata}


if __name__ == '__main__':
    import sys
    CASES[sys.argv[1]]()
    print(json.dumps({'probe_passed': True, 'whole_source_correct': None,
                      'independent_review': 'PENDING'}))
