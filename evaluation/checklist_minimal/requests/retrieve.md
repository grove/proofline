Added way to retrieve existing jobs per tags.

In making extensive use of multiple `tags` on each `Job` (that define multiple configuration settings that define what that job does, as well as manufactured guids) I've encountered the following **need**/*nice-to-have*.

> I'd like to be able to use `schedule.get_jobs(some_tag) ` to retrieve an `iterable` of `Job` instances which I can then use to log/report on the other tags that have been attached. 

If I have functionality that finds `Job`'s that can be periodically removed by comparing against a table of changing guids, but I've used the `tags` to hold the relevant information that I would like to `log` to have a *human readable history* of what `Job`'s were removed, I need a way to get `Job`'s by `tags`. 

The alternative would be to have the `Scheduler.clear(...)` return the list of jobs that it had removed.