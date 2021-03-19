# -*- coding: utf-8 -*-

# telegram bot api key
tg_key = "put key here"

# variable for separating text from script info
zbx_tg_prefix = "zbxtg"
# directory for saving caches, uids, cookies, etc.
zbx_tg_tmp_dir = "/var/tom/data/" + zbx_tg_prefix
zbx_tg_signature = False

zbx_tg_update_messages = True
zbx_tg_matches = {
    "problem": "PROBLEM: ",
    "ok": "OK: "
}

# zabbix server full url
zbx_server = "http://127.0.0.1"
zbx_api_user = "user"
zbx_api_pass = "password"
# True - do not ignore self signed certificates, False - ignore
zbx_api_verify = False

zbx_basic_auth = False
zbx_basic_auth_user = "zabbix"
zbx_basic_auth_pass = "zabbix"

proxy_to_zbx = None
proxy_to_tg = None

# get your key,
# see https://developers.google.com/maps/documentation/geocoding/intro
google_maps_api_key = None

zbx_db_host = "localhost"
zbx_db_database = "zabbix"
zbx_db_user = "zbxtg"
zbx_db_password = "zbxtg"

emoji_map = {
    "s0": "❕",
    "s1": "ℹ️",
    "s2": "⚠️",
    "s3": "🔸",
    "s4": "🛑",
    "s5": "💣",
    "ok": "✅",
    # "s3": "😷",
    # "s4": "🦠",
    # "s5": "🚑",
    # "s4": "🎈",#
    # "s5": "🧨",
    # "ok": "🎄",#
}
