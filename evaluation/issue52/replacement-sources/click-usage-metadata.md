# Add output of get_usage() to get_info_dict()

## Context 

I am generating some of my user-facing documentation using `get_info_dict()`, and was looking for a way to automate the usage as well without having to hardcode it in the docstrings. 

## Potential solution

Using the calls of `get_info_dict()` to add a `usage` key with the value being the output of `get_usage()`.

Other relevant issues: #2762 

## Workaround

For now I'm using `get_info_dict()`, then looping through the context to get groups and commands, and using `get_usage()` on each, then adding it to that dictionary. The code looks something like this (with the for loop matching the structure of my CLI):

```python
    info = ctx.to_info_dict()
    for cmd_n1 in ctx.command.list_commands(ctx):
        cmd2 = ctx.command.get_command(ctx, cmd_n1)
        sub_ctx = ctx._make_sub_context(cmd2)
        usage = cmd2.get_usage(sub_ctx).replace("Usage: ", "")
        info["command"]["commands"][cmd_n1]["usage"] = usage
        if isinstance(cmd2, click.Group):
            # Groups
            for cmd_n2 in cmd2.list_commands(ctx):
                cmd3 = cmd2.get_command(ctx, cmd_n2)
                sub_ctx3 = sub_ctx._make_sub_context(cmd3)
                usage = cmd3.get_usage(sub_ctx3).replace("Usage: ", "")
                info["command"]["commands"][cmd_n1]["commands"][cmd_n2]["usage"] = usage

```


