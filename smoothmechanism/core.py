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


def is_wunderlist_task_due(task, api):
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

# We pass through to the underlying "task" module so a client script only has to import this module
from task import parse_habitica_task_text
from task import parse_wunderlist_task_text
