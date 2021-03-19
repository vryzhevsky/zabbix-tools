# -*- coding: utf-8 -*-

zbx_tg_daemon_enabled = True
zbx_tg_daemon_enabled_ids = [
    -11111111,  # Telegram Group
]
zbx_tg_daemon_ignore_ids = [
]
zbx_tg_daemon_enabled_admin = "@tgaccount"

zbx_users = {
    "apiuser": "apipassword",
}
tg_zbx_mappings = {
    "-11111111": "apiuser",   # Telegram Group
}
