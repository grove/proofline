# Provide a means to override the default timezone in `arrow.get()`

<!--
Thanks for taking the time to submit this feature request.

Please provide us with a detailed description of the potential improvement.
-->

## Feature Request

When providing a date as a string, it's often useful to be able to have it default to the local timezone but also have the ability to override it with a specific timezone. For example, writing `2025-01-01 12:34` for 12:34 PM in the local time, or `2025-01-01 12:34-0800` for 12:34 PM in the `US/Pacific` timezone.

Currently, if you parse a time with an explicit timezone but also provide a `tzinfo` parameter, the timezone will override the parsed time, for example:

```
>>> arrow.get('2025-01-01 00:00-0800',tzinfo='US/Eastern')
<Arrow [2025-01-01T00:00:00-05:00]>
```

One possible workaround is to use `arrow.get` and then look at the resulting object's tzinfo, but this will fail if the time is being explicitly set to UTC:

```
>>> arrow.get('2025-01-01 00:00:00').tzinfo
datetime.timezone.utc
>>> arrow.get('2025-01-01 00:00:00+0000').tzinfo
datetime.timezone.utc
```

and I do not see any way to determine whether the timezone was specified in the string provided to `.get()`, and this information doesn't even seem to be preserved anywhere:

```
>>> arrow.get('2025-01-01 00:00:00+0000').__dict__
{'_datetime': datetime.datetime(2025, 1, 1, 0, 0, tzinfo=datetime.timezone.utc)}
>>> arrow.get('2025-01-01 00:00:00').__dict__
{'_datetime': datetime.datetime(2025, 1, 1, 0, 0, tzinfo=datetime.timezone.utc)}
```

