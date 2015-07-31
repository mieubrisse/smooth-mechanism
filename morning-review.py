# This script will pull down Wunderlist tasks, find the ones slated for today, email them to a given email address, and log them to a file
# TODO Create a Smooth Mechanism client that reads config files and all that jazz so we don't have to pass crap around everywhere

import wunderclient
import sys
import argparse
import json
import datetime
import webbrowser
import urllib
from itertools import chain
import os
import io
import re

# Constants related to sending the office tasks daily status email
OFFICE_LIST_TITLE_PREFIX = "Office/"
EMAIL_SUBJECT_DATE_FORMAT = '%Y/%m/%d'
EMAIL_SUBJECT_FORMAT_STR = "Today's Goals: {}"

# Constants related to writing daily tasks to file
OUTPUT_FILE_DATE_FORMAT = '%Y-%m-%d'
OUTPUT_FILENAME_FORMAT_STR = '{}_tasks.md'

# Constants related to writing the checkpoint file written every morning and (hopefully) cleaned up every night
CHECKPOINT_FILE_DATE_FORMAT = '%Y-%m-%d'
CHECKPOINT_FILENAME_FORMAT_STR = '{}_tasks.checkpoint'

CREDS_FILEPATH_ARGVAR = "creds_filepath"
EMAIL_TARGET_ARGVAR = "email_target_address"
SMOOTH_MECHANISM_DIRPATH_ARGVAR = "smooth_mechanism_dirpath"

DAILY_TASKS_DIRNAME = "daily-tasks"

CREDS_FILE_CLIENT_ID_KEY = "client_id"
CREDS_FILE_ACCESS_TOKEN_KEY = "access_token"

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

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(CREDS_FILEPATH_ARGVAR, metavar="<Wunderlist creds file>", help="JSON file to pull Wunderlist API creds from")
    # TODO Make email address and output file optional args that only get written to if they exist
    parser.add_argument(EMAIL_TARGET_ARGVAR, metavar="<destination email address>", help="email address to mail today's goals to")
    parser.add_argument(SMOOTH_MECHANISM_DIRPATH_ARGVAR, metavar="<Smooth Mechanism dir>", help="root directory of all Smooth Mechanism tracking")
    # TODO file name format
    # TODO other types of output pipes
    return vars(parser.parse_args())

def validate_args(args):
    # TODO Should probably do some Wunderlist connection validation stuff here
    creds_filepath = args[CREDS_FILEPATH_ARGVAR]
    try:
        with open(creds_filepath, 'r'):
            pass
    except IOError:
        print "Unable to open {} for reading".format(creds_filepath)
    # TODO Check to make sure the output dir exists
    # TODO Check to make sure the email is in proper format

def parse_creds_file(creds_filepath):
    ''' Parses the file holding Wunderlist access creds and returns the tuple (client ID, access token) '''
    with open(creds_filepath) as creds_fp:
        creds_obj = json.load(creds_fp)
        return creds_obj[CREDS_FILE_CLIENT_ID_KEY], creds_obj[CREDS_FILE_ACCESS_TOKEN_KEY]

def task_due_filter(task):
    ''' Returns True if the task is due today or prior, False otherwise '''
    if wunderclient.Task.due_date not in task:
        return False
    due_date = datetime.datetime.strptime(str(task[wunderclient.Task.due_date]), wunderclient.DATE_FORMAT).date()
    return due_date <= datetime.date.today()

def parse_task(task):
    ''' Parses the task into an object containing the task's time costing in minutes, flags, and contents, or None if the task could not be parsed '''
    title = task[wunderclient.Task.title]
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

def work_email_formatter(tasks, comment=""):
    ''' 
    Formats only the office tasks from the given list of tasks into a list of bullet points for only the office tasks 
    
    Params:
    tasks -- dict of (Wunderlist list title, [tasks in list...] ) pairs

    Keyword args:
    comment -- comment to put at the top of the email
    '''
    office_tasks_list_of_lists = [ list_tasks for list_title, list_tasks in tasks.iteritems() if list_title.startswith(OFFICE_LIST_TITLE_PREFIX) ]
    office_tasks = list(chain(*office_tasks_list_of_lists))
    # TODO Make filtering functions like this actual functions
    office_tasks = [task for task in office_tasks if SENSITIVE_TASK_FLAG not in parse_task(task)[TASK_FLAGS_KEY]]
    task_formatter = lambda task : u"\u2022 {}".format(task[wunderclient.Task.title])
    task_strs = map(task_formatter, office_tasks)
    return u'{}\n{}'.format(comment, u'\n'.join(task_strs))

def open_work_tasks_email(todays_tasks, addressee):
    '''
    Opens a new email in the default email client for sending today's goals

    todays_tasks -- a dict of Wunderlist list title -> [task..]
    addressee -- addressee to send email to
    '''
    today_str = datetime.date.strftime(datetime.date.today(), EMAIL_SUBJECT_DATE_FORMAT)
    subject_str = EMAIL_SUBJECT_FORMAT_STR.format(today_str)
    body_str = work_email_formatter(todays_tasks).encode('utf8')     # We prefix a newline to give space to write notes every day
    url = 'mailto:{}?subject={}&body={}'.format(addressee, urllib.quote(subject_str), urllib.quote(body_str))
    webbrowser.open(url)

def daily_task_log_formatter(tasks):
    '''
    Formats all tasks into a file written to specified output directory

    Params:
    tasks -- dict of (Wunderlist list title, [tasks in list...] ) pairs
    '''
    task_formatter = lambda task : u'* {}'.format(task[wunderclient.Task.title])
    list_formatter = lambda list_title, tasks : u'{}\n{}'.format('## ' + list_title, u'\n'.join(map(task_formatter, tasks)))
    list_strs = [ list_formatter(list_title, list_tasks) for list_title, list_tasks in tasks.iteritems() ]
    output = '\n\n'.join(list_strs) + '\n'
    return output

def write_daily_tasks_report(tasks, smooth_mechanism_dirpath):
    ''' Writes the daily tasks to a Markdown file '''
    output_dirpath= os.path.join(smooth_mechanism_dirpath, DAILY_TASKS_DIRNAME)
    if not os.path.isdir(output_dirpath):
        os.makedirs(output_dirpath)
    today_str = datetime.date.strftime(datetime.date.today(), OUTPUT_FILE_DATE_FORMAT)
    output_filepath = os.path.join(output_dirpath, OUTPUT_FILENAME_FORMAT_STR.format(today_str))
    with open(output_filepath, 'w') as output_fp:
        output_fp.write(daily_task_log_formatter(tasks))

def write_tasks_checkpoint_file(tasks, smooth_mechanism_dirpath):
    ''' Stores the state of what was set out to be accomplished in the morning, so at the end of the day we can compare '''
    # TODO If we want a full synposis, we're going to have to save ALL tasks because what if I get something done that wasn't on my list? There's no way to identify it.
    # TODO Error-checking, or something
    today_str = datetime.date.strftime(datetime.date.today(), CHECKPOINT_FILE_DATE_FORMAT)
    checkpoint_filepath = os.path.join(smooth_mechanism_dirpath, CHECKPOINT_FILENAME_FORMAT_STR.format(today_str))
    with io.open(checkpoint_filepath, 'w', encoding="utf8") as checkpoint_fp:
        checkpoint_fp.write(json.dumps(tasks, ensure_ascii=False))

def generate_daily_tasks(args):
    ''' Pulls down today's due and overdue tasks from Wunderlist, writes them to file, and drafts a new email with office-only tasks in the default email client to the given email address '''
    creds_filepath = args[CREDS_FILEPATH_ARGVAR]
    email_addressee = args[EMAIL_TARGET_ARGVAR]
    smooth_mechanism_dirpath = args[SMOOTH_MECHANISM_DIRPATH_ARGVAR]

    client_id, access_token = parse_creds_file(creds_filepath)
    client = wunderclient.WunderClient(access_token, client_id)
    wunder_lists = client.get_lists()
    todays_tasks = {}   # Dict mapping list name -> [tasks...] for lists with tasks due today (or before)
    for wunder_list in wunder_lists:
        list_tasks = client.get_tasks(wunder_list[wunderclient.List.id])
        list_due_tasks = filter(task_due_filter, list_tasks)
        if len(list_due_tasks) > 0:
            list_title = wunder_list[wunderclient.List.title]
            todays_tasks[list_title] = list_due_tasks

    open_work_tasks_email(todays_tasks, email_addressee)
    write_daily_tasks_report(todays_tasks, smooth_mechanism_dirpath)
    write_tasks_checkpoint_file(todays_tasks, smooth_mechanism_dirpath)

args = parse_args()
validate_args(args)
generate_daily_tasks(args)
# TODO Do stuff with writing in markdown and it getting put into Google Drive, too
