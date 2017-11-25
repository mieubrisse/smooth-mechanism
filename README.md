# Smooth Mechanism
My GTD system

## Setup (with pyenv-virtualenv)
1. Install pyenv: `brew install pyenv`
1. Install pyenv-virtualenv: `brew install pyenv-virtualenv`
1. Install the latest Python 2 version: `pyenv install $LATEST_PYTHON_2`
1. Create a new virtualenv for running wunderjinx: `pyenv virtualenv $LATEST_PYTHON_2 smooth-mechanism`
1. Activate the virtualenv: `pyenv activate smooth-mechanism`
1. Install dependencies: `pip install wunderpy2 pyexchange`
1. Deactivate the virtualenv: `pyenv deactivate`
1. Create a config directory somewhere in your filesystem to house the smooth-mechanism config
1. Copy `smooth_mechanism_config.py.template` to your config directory, naming it `smooth_mechanism_config.py`
1. Make sure to call all smooth-mechanism CLIs with your config directory in the PYTHONPATH (e.g. `PYTHONPATH=/path/to/your/config/dir:${PYTHONPATH} register-meetings`)

## Register Meetings
Pulls meetings from an Outlook Exchange server and creates a Wunderlist task for each of them.

**NOTE:** There's an error in the pyexchange library with connecting to the exchange server (in its connection.py file) because SSL is forced to be verified. 
See: https://github.com/linkedin/pyexchange/issues/53 for more info.
