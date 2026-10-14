Get next run by tag

It would nice to have an parameter for next_run which takes a tag...
e.g. schedule.next_run(tag) 
which returns the next run information for the given tag parameter.

schedule.every(5).minutes.do(soundMaker).tag('soundMaker')

To get the next time soundMaker would run you could do this...
nextTime = schedule.next_run('soundMaker') 

This could also be used to see if the item is scheduled already or it was canceled.
if schedule.next_run('soundMaker') != None:
    print('it is scheduled') # return True
else:
    print it is not scheduled # return False