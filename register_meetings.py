import wunderpy2
import pyexchange
import datetime
import sys
import re
import math
import os.path
import argparse

# Local imports
# TODO Make this follow relative import format
import config as sm_config

FORWARDED_EVENT_SUBJECT_PREFIX = "FW: "

# Meeting durations will be rounded up to multiples of this number of minutes
DURATION_GRANULARITY = 15

def _format_duration(seconds):
    ''' Rounds the given duration in seconds to the next DURATION_GRANULARITY and formats the duration like so: 1.5h, 1h, 45m, etc. '''
    minutes = seconds / 60
    # Round to next 15m chunk
    minutes = minutes if minutes % DURATION_GRANULARITY == 0 else minutes + (DURATION_GRANULARITY - minutes % DURATION_GRANULARITY)
    if minutes < 60:
        return str(minutes) + "m"
    else:
        hours, leftover = divmod(minutes, 60)
        if leftover == 0:
            return str(hours) + "h"
        else:
            # Practially, if this decimal is anything other than _.5, whoever scheduled the meeting is a dick
            return str(float(minutes) / 60) + "h"

def _format_event(event):
    ''' Formats an event into a Wunderlist title '''
    # Extract event info from subject
    subject = event.subject
    pattern = re.compile("^(FW:)? *( *\[.*\] *)* *(FW:)? *([^ ].*)$")
    matches = pattern.match(subject)
    if matches is None:
        raise ValueError("Could not extract event info from event subject: {}".format(subject))
    event_info = matches.groups()[-1]

    # Extract event duration
    start = event.start
    end = event.end
    duration = end - start;
    pretty_duration = _format_duration(duration.seconds)

    return "{} - Meeting: {}".format(pretty_duration, event_info)

def main(argv=sys.argv):
    # Connect to Outlook
    username = "{}\\{}".format(sm_config.DOMAIN, sm_config.USERNAME)
    connection = pyexchange.ExchangeNTLMAuthConnection(url=sm_config.EXCHANGE_SERVER_URL, username=username, password=sm_config.PASSWORD)
    calendar = pyexchange.Exchange2010Service(connection).calendar()

    # Connect to Wunderlist
    access_token = sm_config.WUNDERLIST_ACCESS_TOKEN
    client_id = sm_config.WUNDERLIST_CLIENT_ID
    wunderlist_api = wunderpy2.WunderApi()
    wunderlist_client = wunderlist_api.get_client(access_token, client_id)

    today = datetime.date.today()
    local_day_start = datetime.datetime.combine(today, datetime.time(0,0))
    local_day_end = datetime.datetime.combine(today, datetime.time(23,59))

    print "INFO: Getting today's meetings from Exchange..."
    todays_events = calendar.list_events(start=local_day_start, end=local_day_end)

    print "INFO: Storing today's meetings in Wunderlist..."
    for event in todays_events.events:
        if event.is_all_day:
            continue
        task_title = _format_event(event)
        task = wunderlist_client.create_task(sm_config.WUNDERLIST_LIST_ID, task_title, due_date=today.strftime(wunderlist_api.DATE_FORMAT))

    # Strip events we're not interested in
    # TODO Filter by 'availability' keyword here, if desired

if __name__ == "__main__":
    sys.exit(main())
