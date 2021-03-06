
import re
from datetime import datetime

def date(s):
    '''Returns a datetime object for the given string

    date() applies a range of known date patterns to parse the string
    '''

    if not s:
        return None

    s = str(s).strip()

    templates = {
        '\d{4}-\d{1,2}-\d{1,2}T\d{1,2}:\d{1,2}:\d{1,2}': '%Y-%m-%dT%H:%M:%S',
        '\d{4}-\d{1,2}-\d{1,2} \d{1,2}:\d{1,2}:\d{1,2}': '%Y-%m-%d %H:%M:%S',

        '\d{4}-\d{1,2}-\d{1,2}': '%Y-%m-%d',
        '\d{4}/\d{1,2}/\d{1,2}': '%Y/%m/%d',

        '\d{1,2}-\d{1,2}-\d{4}': '%d-%m-%Y',
        '\d{1,2}/\d{1,2}/\d{4}': '%d/%m/%Y',

        '\d{1,2}-\w{3}-\d{4}': '%d-%b-%Y',
        '\d{1,2}/\w{3}/\d{4}': '%d/%b/%Y',

        '\d{4}': '%Y',
    }

    for k,v in templates.items():
        if re.search('^'+k+'$', s):
            return datetime.strptime(s, v)

    raise TypeError()
