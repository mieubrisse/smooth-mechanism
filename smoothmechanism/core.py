"""
Description: 
Defines how the Smooth Mechanism system ought to work so tools 
in the ecosystem can take advantage of common functionality

Author: mieubrisse
"""

import wunderpy2
import json
import os.path
import datetime
import re

SENSITIVE_TASK_FLAG = "!"
TASK_FLAGS = [SENSITIVE_TASK_FLAG]
# First group is time costing, second group is flags, third group is task contents
MINUTE_COSTING_INDICATOR = 'm'
HOUR_COSTING_INDICATOR = 'h'
DAY_COSTING_INDICATOR = 'd'
HOURS_IN_DAY = 5    # For the purposes of work costing, 1d = 5h. TODO Because this also needs to handle personal time as well, figure out a better method
COSTING_INDICATOR_PARSER = '[mhdMHD]'   # TODO I probably *should* have this be somethign like MINUTE_COSTING_INDICATOR.lower(), MINUTE_COSTING_INDICATOR.upper()... but, meh
TIME_COSTING_PARSER = '(\d+\.?\d*)({})'.format(COSTING_INDICATOR_PARSER)
TASK_PARSER = '[\[(]?(\d+\.?\d*{})?[)\]]?\s*-?\s*([{}])*\s*(.*)'.format(COSTING_INDICATOR_PARSER, "".join(SENSITIVE_TASK_FLAG))
TASK_COSTING_KEY = 'time_costing'
TASK_FLAGS_KEY = 'flags'
TASK_CONTENTS_KEY = 'contents'

def is_task_due(task, api):
    """ 
    Returns True if the task is due today or prior, False otherwise 

    Args:
    task -- Task to check if due today
    api -- Wunderpy2 API the task came from
    """
    if wunderpy2.Task.DUE_DATE not in task:
        return False
    due_date = datetime.datetime.strptime(str(task[wunderpy2.Task.DUE_DATE]), api.DATE_FORMAT).date()
    return due_date <= datetime.date.today()

def parse_task(task):
    """ 
    Parses the task into an object containing the task's time costing in minutes, flags, and contents, or None if the task could not be parsed 
    """
    title = task[wunderpy2.Task.TITLE]
    match = re.match(TASK_PARSER, title)
    if match is None:
        return None
    costing_str = match.group(1)
    if costing_str is not None:
        time, granularity = re.match(TIME_COSTING_PARSER, costing_str).groups()
        time = float(time)
        granularity_translator = {
                MINUTE_COSTING_INDICATOR : lambda time : int(time),
                HOUR_COSTING_INDICATOR : lambda time : int(time * 60),
                DAY_COSTING_INDICATOR : lambda time : int(time * HOURS_IN_DAY * 60),
                }
        costing = granularity_translator[granularity.lower()](time)
    else:
        costing = 0
    flags_str = match.group(2)
    if flags_str is not None:
        task_flags = [flag for flag in TASK_FLAGS if flag in flags_str]
    else:
        task_flags = []
    return {
            TASK_COSTING_KEY : costing,
            TASK_FLAGS_KEY : task_flags,
            TASK_CONTENTS_KEY : match.group(3),
            }
