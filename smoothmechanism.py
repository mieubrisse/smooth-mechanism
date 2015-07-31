import json
import os.path

def enum(**enums):
    return type('Enum', (), enums)

ConfigKey = enum(
    SMOOTH_MECHANISM_DIRPATH = "smooth_mechanism_dirpath",
    DEST_EMAIL_ADDR = "dest_email_address",
    WUNDERLIST_CLIENT_ID = "wunderlist_client_id",
    WUNDERLIST_ACCESS_TOKEN = "wunderlist_access_token",
    )

def get_config(config_filepath):
    with open(config_filepath) as config_fp:
        return json.load(config_fp)
