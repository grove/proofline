"""UTC calibration controls; public calendar facts, never grader answers."""
import inspect

CLARIFICATION = ('User clarification, 2026-10-12: Ambiguous timestamp strings without an '
                 'interchange agreement raise ValueError; unambiguous ISO forms remain accepted. '
                 'No fixed expanded-year width is authorized.')

# IERS Leap_Second.dat, Bulletin C 72 (July 2026): effective dates after insertions.
EFFECTIVE = ('1972-07-01 1973-01-01 1974-01-01 1975-01-01 1976-01-01 '
             '1977-01-01 1978-01-01 1979-01-01 1980-01-01 1981-07-01 '
             '1982-07-01 1983-07-01 1985-07-01 1988-01-01 1990-01-01 '
             '1991-01-01 1992-07-01 1993-07-01 1994-07-01 1996-01-01 '
             '1997-07-01 1999-01-01 2006-01-01 2009-01-01 2012-07-01 '
             '2015-07-01 2017-01-01').split()


def integer(text):
    sign=-1 if text.startswith('-') else 1
    text=text.lstrip('+-');value=0
    for start in range(0,len(text),9):
        chunk=text[start:start+9];value=value*10**len(chunk)+int(chunk)
    return sign*value


def year_text(year):
    # Chunk conversion also avoids Python's decimal-string size restriction.
    value=abs(year);chunks=[]
    while value:
        value,chunk=divmod(value,10**9);chunks.append(chunk)
    digits=(str(chunks[-1])+''.join(f'{x:09}' for x in reversed(chunks[:-1]))) if chunks else '0'
    if 0<=year<=9999:return digits.zfill(4)
    return ('-' if year<0 else '+')+digits.zfill(6)


def day_number(year,month,day):
    year-=month<=2;era=year//400;within=year-era*400
    shifted=month-3 if month>2 else month+9
    return era*146097+within*365+within//4-within//100+(153*shifted+2)//5+day-1


def civil(number):
    era,day=divmod(number,146097)
    year=(day-day//1460+day//36524-day//146096)//365
    remainder=day-(365*year+year//4-year//100)
    month=(5*remainder+2)//153
    date=remainder-(153*month+2)//5+1
    month+=3 if month<10 else -9
    return era*400+year+(month<=2),month,date


def regex_process(data):
    import re
    if not isinstance(data,str):raise ValueError('ISO timestamp required')
    data=str.__str__(data)
    if data.count('T')!=1:raise ValueError('ISO timestamp required')
    date,clock=data.split('T')
    date=date[:1].replace('\u2212','-')+date[1:].replace('\u2010','-')
    clock=clock.replace('\u2212','-')
    extended=[r'([+-][0-9]{4,}|[0-9]{4})-([0-9]{2})-([0-9]{2})',
              r'([+-][0-9]{4,}|[0-9]{4})-([0-9]{3})',
              r'([+-][0-9]{4,}|[0-9]{4})-W([0-9]{2})-([1-7])']
    basic=[r'([+-][0-9]{4,}|[0-9]{4})([0-9]{2})([0-9]{2})',
           r'([+-][0-9]{4,}|[0-9]{4})([0-9]{3})',
           r'([+-][0-9]{4,}|[0-9]{4})W([0-9]{2})([1-7])']
    candidates=set()
    for style,patterns in ((True,extended),(False,basic)):
        for kind,pattern in enumerate(patterns):
            match=re.fullmatch(pattern,date)
            if not match:continue
            year=integer(match[1]);first=day_number(year,1,1)
            if match[1].startswith('-') and year==0:continue
            if kind==0:
                month,day=int(match[2]),int(match[3]);number=day_number(year,month,day)
                if not 1<=month<=12 or civil(number)!=(year,month,day):continue
            elif kind==1:
                ordinal=int(match[2]);number=first+ordinal-1
                if ordinal<1 or number>=day_number(year+1,1,1):continue
            else:
                week,weekday=int(match[2]),int(match[3])
                jan4=first+3;start=jan4-(jan4-day_number(1970,1,5))%7
                next4=day_number(year+1,1,4);end=next4-(next4-day_number(1970,1,5))%7
                number=start+(week-1)*7+weekday-1
                if week<1 or number>=end:continue
            candidates.add((style,number))
    if not candidates:raise ValueError('Invalid ISO date')
    style=next(iter(candidates))[0]
    zone=re.search(r'(Z|[+-][0-9]{2}(?::?[0-9]{2})?)\Z',clock)
    if not zone:raise ValueError('Explicit ISO offset required')
    offset=0;shift=zone[1]
    if shift!='Z':
        digits=shift[1:].replace(':','');hours=int(digits[:2]);minutes=int(digits[2:] or '0')
        if hours>23 or minutes>59 or (':' in shift and not style) or style and len(digits)==4 and ':' not in shift:
            raise ValueError('Invalid offset')
        offset=(hours*60+minutes)*60*(1 if shift[0]=='+' else -1)
        if shift[0]=='-' and offset==0:raise ValueError('ISO zero offset requires a plus sign or Z')
    pattern=(r'([0-9]{2})(?::([0-9]{2})(?::([0-9]{2}))?)?' if style else
             r'([0-9]{2})(?:([0-9]{2})(?:([0-9]{2}))?)?')
    match=re.fullmatch(pattern+r'(?:[.,]([0-9]+))?',clock[:zone.start()])
    if not match:raise ValueError('Invalid time representation')
    hour=int(match[1]);minute=int(match[2] or '0');second=int(match[3] or '0')
    fraction=match[4];unit=1 if match[3] else 60 if match[2] else 3600
    if hour>24 or minute>59 or second>60:raise ValueError('Invalid clock component')
    if hour==24 and (minute or second or fraction and any(c!='0' for c in fraction)):
        raise ValueError('End-of-day time must have zero lower components')
    base_seconds=hour*3600+minute*60+min(second,59)-offset
    outputs=set()
    for _,number in candidates:
        leap=second==60;seconds=base_seconds
        if fraction:
            days,position=divmod(seconds,86400);distance=86400-position
            inserted=unit>1 and distance<=unit and civil(number+days+1) in LEAP_EFFECTIVE
            elapsed=integer(fraction)*(unit+inserted)//10**len(fraction)
            if inserted and elapsed>=distance:
                leap=elapsed==distance;elapsed-=1
            seconds+=elapsed
        days,seconds=divmod(seconds,86400);number+=days
        year,month,day=civil(number);out_hour,seconds=divmod(seconds,3600);out_minute,out_second=divmod(seconds,60)
        if leap:
            if (out_hour,out_minute,out_second)!=(23,59,59) or civil(number+1) not in LEAP_EFFECTIVE:continue
            out_second=60
        outputs.add(f'{year_text(year)}-{month:02}-{day:02}T{out_hour:02}:{out_minute:02}:{out_second:02}Z')
    if len(outputs)!=1:raise ValueError('Invalid or ambiguous complete ISO timestamp; an interchange agreement is required')
    return outputs.pop()


def scan_process(data):
    from datetime import date, timedelta
    from fractions import Fraction
    if not isinstance(data,str):raise TypeError('ISO timestamp required')
    data=str.__str__(data)
    if data.count('T')!=1:raise TypeError('ISO timestamp required')
    calendar,time=data.split('T')
    calendar=calendar[:1].replace('\u2212','-')+calendar[1:].replace('\u2010','-')
    time=time.replace('\u2212','-')
    def digits(text):
        if not text or any(c not in '0123456789' for c in text):raise ValueError('ASCII digits required')
        return integer(text)
    sign=calendar[0] if calendar[:1] in ('+','-') else ''
    rest=calendar[len(sign):];style='-' in rest
    if style:forms=[rest.split('-')]
    elif 'W' in rest:
        prefix,tail=rest.split('W',1);forms=[[prefix,'W'+tail[:2],tail[2:]]]
    elif sign:forms=[[rest[:-4],rest[-4:-2],rest[-2:]],[rest[:-3],rest[-3:]]]
    else:
        tail=rest[4:];forms=[[rest[:4],tail[:2],tail[2:]]] if len(tail)==4 else [[rest[:4],tail]]
    candidates={}
    for parts in forms:
        try:
            if len(parts[0])<4 or not sign and len(parts[0])!=4:continue
            year=digits(parts[0])*(-1 if sign=='-' else 1)
            if sign=='-' and year==0:continue
            components=parts[1:];mapped=2000+year%400;cycle=year-mapped
            if len(components)==2 and components[0].startswith('W'):
                if len(components[0])!=3 or len(components[1])!=1:continue
                point=date.fromisocalendar(mapped,digits(components[0][1:]),digits(components[1]))
            elif len(components)==2:
                if any(len(x)!=2 for x in components):continue
                point=date(mapped,digits(components[0]),digits(components[1]))
            elif len(components)==1 and len(components[0])==3:
                ordinal=digits(components[0]);point=date(mapped,1,1)+timedelta(days=ordinal-1)
                if ordinal<1 or point.year!=mapped:continue
            else:continue
            candidates[(point.year+cycle,point.month,point.day)]=(point,cycle)
        except ValueError:continue
    if not candidates:raise TypeError('Invalid ISO date')
    if time.endswith('Z'):clock=time[:-1];offset=0
    else:
        positions=[i for i,c in enumerate(time) if c in '+-']
        if len(positions)!=1:raise ValueError('Explicit offset required')
        index=positions[0];clock=time[:index];zone=time[index+1:]
        if ':' in zone:
            pieces=zone.split(':')
            if not style or len(pieces)!=2 or any(len(x)!=2 for x in pieces):raise ValueError('Invalid offset')
        elif len(zone) in (2,4) and not (style and len(zone)==4):pieces=[zone[:2],zone[2:] or '00']
        else:raise ValueError('Invalid offset')
        oh,om=map(digits,pieces)
        if oh>23 or om>59:raise ValueError('Invalid offset')
        offset=(oh*3600+om*60)*(1 if time[index]=='+' else -1)
        if time[index]=='-' and offset==0:raise ValueError('ISO zero offset requires a plus sign or Z')
    decimal=[i for i,c in enumerate(clock) if c in '.,']
    if len(decimal)>1:raise ValueError('Invalid fraction')
    fraction=Fraction(0)
    if decimal:
        index=decimal[0];text=clock[index+1:];fraction=Fraction(digits(text),10**len(text));clock=clock[:index]
    if ':' in clock:
        pieces=clock.split(':')
        if not style or len(pieces) not in (2,3):raise ValueError('Invalid time')
    else:
        if len(clock) not in (2,4,6) or style and len(clock)>2:raise ValueError('Invalid time')
        pieces=[clock[i:i+2] for i in range(0,len(clock),2)]
    if any(len(x)!=2 for x in pieces):raise ValueError('Invalid time')
    values=list(map(digits,pieces));h=values[0];m=values[1] if len(values)>1 else 0;s=values[2] if len(values)>2 else 0
    if h>24 or m>59 or s>60 or h==24 and (m or s or fraction):raise ValueError('Invalid clock component')
    base_seconds=h*3600+m*60+min(s,59)-offset;unit=(3600,60,1)[len(values)-1]
    outputs=set()
    for point,cycle in candidates.values():
        leap=s==60;duration=unit
        start_days,start_second=divmod(base_seconds,86400)
        next_day=point+timedelta(days=start_days+1)
        until_leap=86400-start_second
        if unit>1 and until_leap<=unit and (next_day.year+cycle,next_day.month,next_day.day) in LEAP_EFFECTIVE:
            duration+=1
        elapsed=int(fraction*duration)
        if duration>unit and elapsed>=until_leap:
            leap=elapsed==until_leap;elapsed-=1
        days,seconds=divmod(base_seconds+elapsed,86400);point+=timedelta(days=days)
        y,month,day=point.year+cycle,point.month,point.day
        hour,seconds=divmod(seconds,3600);minute,second=divmod(seconds,60)
        if leap:
            following=point+timedelta(days=1)
            if (hour,minute,second)!=(23,59,59) or (following.year+cycle,following.month,following.day) not in LEAP_EFFECTIVE:continue
            second=60
        outputs.add(f'{year_text(y)}-{month:02}-{day:02}T{hour:02}:{minute:02}:{second:02}Z')
    if not outputs:raise TypeError('Invalid complete ISO timestamp')
    if len(outputs)>1:raise ValueError('Ambiguous complete ISO timestamp; an interchange agreement is required')
    return outputs.pop()


def program(variant):
    metadata='# Public IERS leap-second effective dates, Bulletin C 72.\nLEAP_EFFECTIVE = '+repr(
        {tuple(map(int,value.split('-'))) for value in EFFECTIVE})+'\n\n'
    common=inspect.getsource(integer)+'\n'+inspect.getsource(year_text)+'\n'
    if variant=='good':
        return metadata+common+inspect.getsource(day_number)+'\n'+inspect.getsource(civil)+'\n'+inspect.getsource(regex_process).replace('def regex_process(', 'def process(')
    if variant=='alternative':return metadata+common+inspect.getsource(scan_process).replace('def scan_process(', 'def process(')
    raise ValueError('Unknown UTC reference')
