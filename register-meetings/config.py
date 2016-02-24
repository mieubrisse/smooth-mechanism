import yaml

# TODO Make this not hardcoded
_config_fp = open("config.yaml")
_config = yaml.load(_config_fp)

EXCHANGE_SERVER_URL = _config["exchange_server_url"]
DOMAIN = _config["domain"]
USERNAME = _config["username"]
PASSWORD = _config["password"]
WUNDERLIST_LIST_ID = _config["wunderlist_list_id"]
