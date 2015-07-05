import urllib3
import requests
import sys
import json

# TODO Debugging only
from pprint import pprint


def ensure_not_empty(params):
    ''' Check that the values in the given dict of (pretty param name -> value) is not None or empty. '''
    for pretty_name, value in params.iteritems():
        if value is None or not value.strip():
            raise ValueError('{} cannot be null or empty'.format(pretty_name))

# All times are UTC time
DATE_FORMAT = '%Y-%m-%d'
DATETIME_FORMAT = '%Y-%m-%dT%H:%M:%SZ'
_API_URL = 'http://a.wunderlist.com/api'

class _Endpoints:
    tasks = "tasks"
    lists = "lists"

# TODO Unsure if I like having all the values recorded or dislike that it's now set in code
class _WunderlistObj:
    id = 'id'
    revision = 'revision'

class List(_WunderlistObj):
    ''' POPO to contain list JSON keys '''
    title = 'title'
    creation_timestamp = 'created_at'
    type = 'list_type'

class Task(_WunderlistObj):
    ''' POPO to contain task JSON keys '''
    assignee_id = 'assignee_id'
    assigner_id = 'assigner_id'
    creation_timestamp = 'created_at'
    creator_id = 'created_by_id'
    due_date = 'due_date'
    list_id = 'list_id'
    starred = 'starred'  # boolean
    title = 'title'
    type = 'type'
    completed = 'completed' # boolean
    creation_request_id = 'created_by_request_id'

class WunderClient:
    ''' Client for accessing the Wunderlist info of a user (given by the access token) '''
    @staticmethod
    def _validate_response(response):
        # TODO Fill this out using the error codes here: https://developer.wunderlist.com/documentation/concepts/formats
        if response.status_code != 200:
            raise ValueError('{} {}'.format(response.status_code, str(response.json())))


    def __init__(self, access_token, client_id, api_version='1'):
        '''
        Create a Wunderlist client with the given parameters.

        access_token -- Wunderlist access token, given once a user has given Wunderlist permission access their data
        client_id -- Wunderlist-generated ID for the app accessing the client's data

        Keyword args:
        api_version -- Version of the Wunderlist API
        '''

        # Sanity checks
        ensure_not_empty({ 'access token' : access_token, 'client_id' : client_id })

        self.client_id = client_id
        self.access_token = access_token
        self.api_version = api_version

    def _wunderlist_request(self, endpoint, method='GET', params=None, data=None):
        '''
        Helper to form a request to the Wunderlist API

        method -- GET, PUT, PATCH, etc.
        url_fragment -- trailing portion URL to be appended after the API version
        '''
        headers = {
                'X-Access-Token' : self.access_token,
                'X-Client-ID' : self.client_id
                }
        if method in ['POST', 'PATH', 'PUT']:
            headers['Content-Type'] = 'application/json'
        url = '/'.join([_API_URL, 'v' + self.api_version, endpoint])
        response = requests.request(method=method, url=url, params=params, headers=headers, data=data)
        WunderClient._validate_response(response)
        return response

    def get_lists(self):
        ''' Gets all the client's lists '''
        response = self._wunderlist_request(_Endpoints.lists)
        return response.json()

    def get_list(self, list_id):
        ''' Gets the given list '''
        endpoint = '/'.join([_Endpoints.lists, str(list_id)])
        response = self._wunderlist_request(endpoint)
        return response.json()

    def create_list(self, title):
        # TODO https://developer.wunderlist.com/documentation/endpoints/list
        pass

    def update_list(self, new_list_obj, revision):
        # TODO https://developer.wunderlist.com/documentation/endpoints/list
        pass

    def make_list_public(self, list_id, revision):
        # TODO https://developer.wunderlist.com/documentation/endpoints/list
        pass

    def delete_list(self, list_id, revision):
        # TODO https://developer.wunderlist.com/documentation/endpoints/list
        pass

    def get_tasks(self, list_id, completed=False):
        ''' Gets un/completed tasks for the given list ID '''
        params = { Task.list_id : str(list_id), Task.completed : completed }
        response = self._wunderlist_request(_Endpoints.tasks, params=params)
        return response.json()

    def get_task(self, task_id):
        ''' Gets task information for the given ID '''
        endpoint = '/'.join(_Endpoints.tasks, str(task_id))
        response = self._wunderlist_request(endpoint)
        return response.json()

    def create_task(self, task_id):
        # TODO https://developer.wunderlist.com/documentation/endpoints/task
        pass

    def update_task(self, task_id):
        # TODO https://developer.wunderlist.com/documentation/endpoints/task
        pass

    def delete_task(self, task_id, revision):
        # TODO https://developer.wunderlist.com/documentation/endpoints/task
        pass

if __name__ == '__main__':
    client = WunderClient(sys.argv[1], sys.argv[2])
    lists = client.get_lists()
    list_id = lists[0][List.id]
    tasks = client.get_tasks(list_id, completed=False)
    task_id = tasks[0][Task.id]
    print json.dumps(tasks)

