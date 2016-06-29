"""
Description:
Defines what a Smooth Mechanism task contains, and how to get one from the representations stored in things like Wunderlist, Habitica, etc.

Author: mieubrisse
"""
import re

SENSITIVE_TASK_FLAG = "!"
TASK_FLAGS = [SENSITIVE_TASK_FLAG]
# First group is time costing, second group is flags, third group is task contents
MINUTE_COSTING_INDICATOR = 'm'
HOUR_COSTING_INDICATOR = 'h'
DAY_COSTING_INDICATOR = 'd'
HOURS_IN_DAY = 5    # For the purposes of work costing, 1d = 5h. TODO Because this also needs to handle personal time as well, figure out a better method
COSTING_INDICATOR_PARSER = '[mhdMHD]'   # TODO I probably *should* have this be somethign like MINUTE_COSTING_INDICATOR.lower(), MINUTE_COSTING_INDICATOR.upper()... but, meh

TIME_COSTING_PARSER = '(\d+\.?\d*)({})'.format(COSTING_INDICATOR_PARSER) # Used for splitting a time costing into number and granularity components
TASK_COSTING_KEY = 'time_costing'
TASK_FLAGS_KEY = 'flags'
TASK_CONTENTS_KEY = 'contents'

class SMTask:
    """
    Class representing the data contained inside of a task in the Smooth Mechanism system
    """
    def __init__(self, costing, flags, contents):
        self.costing = costing
        self.flags = flags
        self.contents = contents

class GenericTaskParser:
    PARSER_REGEX = '[\[(]?(\d+\.?\d*{})?[)\]]?\s*-?\s*([{}]*)\s*(.*)'.format(COSTING_INDICATOR_PARSER, "".join(TASK_FLAGS))

    @staticmethod
    def translate_parse_results(matches):
        """
        Required function to translate the parse results into a tuple of (costing str, flags str, and task text)
        """
        return (matches.group(1), matches.group(2), matches.group(3))

# TODO We're not using this for now, since the regex is annoying
# class HabiticaTaskParser:
#     PARSER_REGEX = '([{}]*)\s*(.*)\s+(?:\((\d+\.?\d*{})\))?'.format("".join(TASK_FLAGS), COSTING_INDICATOR_PARSER)
#
#     @staticmethod
#     def translate_parse_results(matches):
#         """
#         Required function to translate the parse results into a tuple of (costing str, flags str, and task text)
#         """
#         return (matches.group(3), matches.group(1), matches.group(2))

def _parse_task_text(text, task_parser):
    """
    Helper method to use the given parser to decompose a task text into an object containing the task's:
    1) Costing (in minutes)
    2) Flags (if any)
    3) Task text
    """
    match = re.match(task_parser.PARSER_REGEX, text)
    if match is None:
        return None
    costing_str, flags_str, task_contents_str = task_parser.translate_parse_results(match)

    # TODO Debugging
    print (costing_str, flags_str, task_contents_str)

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

    if flags_str is not None:
        task_flags = [flag for flag in TASK_FLAGS if flag in flags_str]
    else:
        task_flags = []

    return SMTask(costing, task_flags, task_contents_str)

def parse_wunderlist_task_text(text):
    return _parse_task_text(text, GenericTaskParser)

def parse_habitica_task_text(text):
    return _parse_task_text(text, GenericTaskParser)
