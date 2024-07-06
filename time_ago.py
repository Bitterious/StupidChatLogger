from datetime import datetime
from math import floor
def time_ago(time=False):
    """
    Get a datetime object or a int() Epoch timestamp and return a
    pretty string like 'an hour ago', 'Yesterday', '3 months ago',
    'just now', etc

    Modified from: http://stackoverflow.com/a/1551394/141084
    """
    now = datetime.now()
    if type(time) is int:
        diff = now - datetime.fromtimestamp(time)
    elif isinstance(time,datetime):
        diff = now - time
    elif not time:
        diff = now - now
    else:
        raise ValueError('invalid date %s of type %s' % (time, type(time)))
    second_diff = diff.seconds
    day_diff = diff.days

    if day_diff < 0:
        return ''

    if day_diff == 0:
        if second_diff < 10:
            return "just now"
        if second_diff < 60:
            return str(second_diff) + " seconds ago"
        if second_diff < 120:
            return  "a minute ago"
        if second_diff < 3600:
            return str(second_diff // 60) + " minutes ago"
        if second_diff < 7200:
            return "an hour ago"
        if second_diff < 86400:
            return str( second_diff // 3600 ) + " hours ago"
    if day_diff == 1:
        return "Yesterday"
    if day_diff < 7:
        return str(floor(day_diff)) + " days ago"
    if day_diff < 31:
        return str(day_diff//7) + " weeks ago"
    if day_diff < 365:
        return str(day_diff//30) + " months ago"
    return str(day_diff//365) + " years ago"