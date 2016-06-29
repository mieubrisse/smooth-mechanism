"""
Description: Creates Habitica dailies in Wunderlist and tracks their IDs for later checking-off
Author: mieubrisse
"""
 
import sys
import argparse
import wunderpy2
import requests

import config as sm_config

_HABITICA_BASE_URL = "https://habitica.com/api/v3"
_HABITICA_HEADERS = {
        "Content-Type": "application/json",
        "x-api-user": sm_config.HABITICA_CLIENT_ID,
        "x-api-key": sm_config.HABITICA_ACCESS_TOKEN
        }
 
def _parse_args(argv):
    """ Parses args into a dict of ARGVAR=value, or None if the argument wasn't supplied """
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    # parser.add_argument(_SAMPLE_ARGVAR, metavar="<sample>", help="This variable is a sample variable")
    return vars(parser.parse_args(argv))
 
def _print_error(msg):
    sys.stderr.write('Error: ' + msg + '\n')
 
def _validate_args(args):
    """ Performs validation on the given args dict, returning a non-zero exit code if errors were found or None if all is well """
    return None
 
def main(argv):
    args = _parse_args(map(str, argv))
    err_code = _validate_args(args)
    if err_code is not None:
        return err_code

    try:
        response = requests.get(_HABITICA_BASE_URL + "/tasks/user?type=dailys", headers=_HABITICA_HEADERS)
    except requests.RequestException:
        _print_error("An exception occurred while connecting to Habitica")
        return 1
    if response.status_code != 200:
        _print_error("Got a non-200 response from Habitica: " + str(response.status_code))
        return 2
    response_obj = response.json()
    if 'data' not in response_obj:
        _print_error("No data returned when requesting Habitica dailies")
        retrun 3
    dailies = response_obj['data']
    for daily in dailies:
        # TODO Things around checking whether the daily is due today 

    wunderclient = wunderpy2.WunderApi().get_client(sm_config.WUNDERLIST_ACCESS_TOKEN, sm_config.WUNDERLIST_CLIENT_ID)
 
    return 0
 
if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
