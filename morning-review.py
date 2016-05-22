# This script will pull down Wunderlist tasks, find the ones slated for today, email them to a given email address, and log them to a file
# TODO Create a Smooth Mechanism client that reads config files and all that jazz so we don't have to pass crap around everywhere

import wunderpy2
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

# Local imports
import smoothmechanism.core as sm_core
import config as sm_config

# Constants related to sending the work tasks daily status email
LIST_TITLE_PREFIXES = [ "Onsite/", "Office/" ]  # Which lists do we send an email for?
EMAIL_SUBJECT_DATE_FORMAT = '%Y/%m/%d'
EMAIL_SUBJECT_FORMAT_STR = "Today's Goals: {}"
EMAIL_TASK_FORMATTER = lambda task : u"\u2022 {}".format(task[wunderpy2.Task.TITLE])

# Constants related to writing daily tasks to file
OUTPUT_FILE_DATE_FORMAT = '%Y-%m-%d'
OUTPUT_FILENAME_FORMAT_STR = '{}_tasks.md'
DAILY_TASK_LOG_TASK_FORMATTER = lambda task : u'* {}'.format(task[wunderpy2.Task.TITLE])

# Constants related to writing the checkpoint file written every morning and (hopefully) cleaned up every night
CHECKPOINT_FILE_DATE_FORMAT = '%Y-%m-%d'
CHECKPOINT_FILENAME_FORMAT_STR = '{}_tasks.checkpoint'

CONFIG_FILEPATH_ARGVAR = "config_filepath"
EMAIL_TARGET_ARGVAR = "email_target_address"
SMOOTH_MECHANISM_DIRPATH_ARGVAR = "smooth_mechanism_dirpath"

DAILY_TASKS_DIRNAME = "daily-tasks"

def _parse_args(argv):
    """ Parses args into a dict of ARGVAR=value, or None if the argument wasn't supplied """
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    # TODO Add arguments here, e.g.:
    # parser.add_argument(_SAMPLE_ARGVAR, metavar="<sample>", help="This variable is a sample variable")
    return vars(parser.parse_args(argv))

def _validate_args(args):
    """ Performs validation on the given args dict, returning a non-zero exit code if errors were found or None if all is well """
    # TODO Should probably do some Wunderlist connection validation stuff here
    # TODO Check to make sure the output dir exists
    # TODO Check to make sure the email is in proper format
    return None

def work_email_formatter(tasks, api):
    ''' 
    Formats only the office tasks from the given list of tasks into a list of bullet points for only the office tasks 
    
    Params:
    tasks -- dict of (Wunderlist list title, [tasks in list...] ) pairs
    api -- Wunderpy2 API that the tasks were retrieved with

    Keyword args:
    comment -- comment to put at the top of the email

    Return:
    Text of email containing work tasks
    '''
    list_tasks = {}
    sections_text = []
    for list_title_prefix in LIST_TITLE_PREFIXES:
        work_tasks_list_of_lists = [ list_tasks for list_title, list_tasks in tasks.iteritems() if list_title.startswith(list_title_prefix) ]
        work_tasks = list(chain(*work_tasks_list_of_lists))

        # TODO Make the functions that get applied to a task for a flag a first-class thing in the code, instead of hardcoding the behaviour here
        work_tasks = [task for task in work_tasks if sm_core.SENSITIVE_TASK_FLAG not in sm_core.parse_task(task)[sm_core.TASK_FLAGS_KEY]]
        task_strs = map(EMAIL_TASK_FORMATTER, work_tasks)
        section_header = list_title_prefix.strip('/') + ':'
        sections_text.append(u'{}\n{}'.format(section_header, u'\n'.join(task_strs)))

    return u'\n\n'.join(sections_text)

def open_work_tasks_email(todays_tasks, api, addressee):
    '''
    Opens a new email in the default email client for sending today's goals

    Args:
    todays_tasks -- a dict of Wunderlist list title -> [task..]
    api -- Wunderpy2 API that the tasks were retrieved with
    addressee -- addressee to send email to
    '''
    today_str = datetime.date.strftime(datetime.date.today(), EMAIL_SUBJECT_DATE_FORMAT)
    subject_str = EMAIL_SUBJECT_FORMAT_STR.format(today_str)
    body_str = work_email_formatter(todays_tasks, api).encode('utf8')     # We prefix a newline to give space to write notes every day
    url = 'mailto:{}?subject={}&body={}'.format(addressee, urllib.quote(subject_str), urllib.quote(body_str))
    webbrowser.open(url)

def daily_task_log_formatter(tasks):
    '''
    Formats all tasks into a file written to specified output directory

    Params:
    tasks -- dict of (Wunderlist list title, [tasks in list...] ) pairs

    Return:
    Body to write to 
    '''
    list_formatter = lambda list_title, tasks : u'{}\n{}'.format('## ' + list_title, u'\n'.join(map(DAILY_TASK_LOG_TASK_FORMATTER, tasks)))
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

def main(argv):
    ''' Pulls down today's due and overdue tasks from Wunderlist, writes them to file, and drafts a new email with office-only tasks in the default email client to the given email address '''
    args = _parse_args(map(str, argv))
    err_code = _validate_args(args)
    if err_code is not None:
        return err_code

    client_id = sm_config.WUNDERLIST_CLIENT_ID
    access_token = sm_config.WUNDERLIST_ACCESS_TOKEN
    email_addressee = sm_config.DEST_EMAIL_ADDR
    smooth_mechanism_dirpath = os.path.abspath(os.path.expanduser(sm_config.SMOOTH_MECHANISM_DIRPATH))

    api = wunderpy2.WunderApi()
    client = api.get_client(access_token, client_id)
    wunder_lists = client.get_lists()
    todays_tasks = {}   # Dict mapping list name -> [tasks...] for lists with tasks due today (or before)
    task_due_filter = lambda task: sm_core.is_task_due(task, api)
    for wunder_list in wunder_lists:
        list_tasks = client.get_tasks(wunder_list[wunderpy2.List.ID])
        list_due_tasks = filter(task_due_filter, list_tasks)
        if len(list_due_tasks) > 0:
            list_title = wunder_list[wunderpy2.List.TITLE]
            todays_tasks[list_title] = list_due_tasks

    open_work_tasks_email(todays_tasks, api, email_addressee)
    write_daily_tasks_report(todays_tasks, smooth_mechanism_dirpath)
    write_tasks_checkpoint_file(todays_tasks, smooth_mechanism_dirpath)

    # TODO Do stuff with writing in markdown and it getting put into Google Drive, too
    return 0

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
