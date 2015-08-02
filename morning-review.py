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
import smoothmechanism as sm

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

CONFIG_FILEPATH_ARGVAR = "config_filepath"
EMAIL_TARGET_ARGVAR = "email_target_address"
SMOOTH_MECHANISM_DIRPATH_ARGVAR = "smooth_mechanism_dirpath"

DAILY_TASKS_DIRNAME = "daily-tasks"


def parse_args():
    ''' Parse command line arguments '''
    parser = argparse.ArgumentParser()
    parser.add_argument(CONFIG_FILEPATH_ARGVAR, metavar="<Smooth Mechanism config file>", default="config.json", help="JSON file to pull Smooth Mechanism config from [default: config.json]")
    # TODO file name format
    # TODO other types of output pipes
    return vars(parser.parse_args())

def validate_args(args):
    ''' Validates command line args in one place '''
    # TODO Should probably do some Wunderlist connection validation stuff here
    config_filepath = args[CONFIG_FILEPATH_ARGVAR]
    try:
        with open(config_filepath, 'r'):
            pass
    except IOError:
        print "Unable to open config file for reading: {}".format(config_filepath)
    # TODO Check to make sure the output dir exists
    # TODO Check to make sure the email is in proper format


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
    office_tasks = [task for task in office_tasks if sm.SENSITIVE_TASK_FLAG not in sm.parse_task(task)[sm.TASK_FLAGS_KEY]]
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
    config_filepath = args[CONFIG_FILEPATH_ARGVAR]
    sm_config = sm.get_config(config_filepath)
    client_id = sm_config[sm.ConfigKey.WUNDERLIST_CLIENT_ID]
    access_token = sm_config[sm.ConfigKey.WUNDERLIST_ACCESS_TOKEN]
    email_addressee = sm_config[sm.ConfigKey.DEST_EMAIL_ADDR]
    smooth_mechanism_dirpath = os.path.abspath(os.path.expanduser(sm_config[sm.ConfigKey.SMOOTH_MECHANISM_DIRPATH]))

    client = wunderclient.WunderClient(access_token, client_id)
    wunder_lists = client.get_lists()
    todays_tasks = {}   # Dict mapping list name -> [tasks...] for lists with tasks due today (or before)
    for wunder_list in wunder_lists:
        list_tasks = client.get_tasks(wunder_list[wunderclient.List.id])
        list_due_tasks = filter(sm.task_due_filter, list_tasks)
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
