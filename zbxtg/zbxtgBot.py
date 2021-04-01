#!/usr/bin/env python3
# coding: utf-8

import sys
import os
import random
import string
import hashlib
import re
import json
import time
from os.path import dirname
import zbxtg_settings
import zbxtg_daemon
import zbxtg
import requests
#from pyzabbix import ZabbixAPI, ZabbixAPIException

commands = [
    "/chatid - ID чата",
    "/alerts - список текущих проблем со средним приоритетом",
    "/problems - список текущих проблем с высоким приоритетом",
    "/inventory - выгрузка списка оборудования",
    "/help - справочник команд",
    # "/graph",
    # "/history",
    # "/screen"
]

def print_message(string):
    string = str(string) + "\n"
    filename = sys.argv[0].split("/")[-1]
    sys.stderr.write(filename + ": " + string)


def file_write(filename, text):
    with open(filename, "w") as fd:
        fd.write(str(text))
    return True

def file_read(filename):
    with open(filename, 'r') as fd:
        text = fd.readlines()
    return text

def cmd_help(reply_text):
    reply_text.append("Привет! Это {0}".format(me['result']['first_name']))
    reply_text.append("Доступные команды:")
    reply_text.append("\n".join(commands))
    tg.disable_web_page_preview = True

def cmd_problems(reply_text, zbx):
    #reply_text.append("Проблем нет. Хорошего дня!")
    #return
    triggers = zbx.get_triggers_active()
    if triggers:
        mytgs = json.loads(triggers)
        if "result" in mytgs:
            for t in mytgs['result']:
                reply_text.append("{{{{s{0}}}}} <strong>{2}</strong> - {1}".format(
                    t["priority"], t["description"], t["hosts"][0]["name"]
                ))
    else:
        reply_text.append("Проблем нет. Хорошего дня!")
    return reply_text

def cmd_alerts(reply_text, zbx):
    #reply_text.append("Проблем нет. Хорошего дня!")
    #return
    triggers = zbx.get_triggers_active(priority=3)
    if triggers:
        mytgs = json.loads(triggers)
        if "result" in mytgs:
            for t in mytgs['result']:
                reply_text.append("{{{{s{0}}}}} <strong>{2}</strong> - {1}".format(
                    t["priority"], t["description"], t["hosts"][0]["name"]
                ))
    else:
        reply_text.append("Алертов нет. Хорошего дня!")
    return reply_text

def cmd_inventory(reply_text, zbx):
    #reply_text.append("Проблем нет. Хорошего дня!")
    #return
    inventory = zbx.get_inventory()
    reply_file = None
    if inventory:
        myinv = json.loads(inventory)
        if "result" in myinv:
            reply_text.append("Инвентарная информация во вложении")

            reply_file = "/tmp/zbxtg_inv."
            reply_file += "".join(random.choice(string.ascii_lowercase + string.digits) for _ in range(10))
            reply_file += ".txt"
            with open(reply_file, 'w') as fp:
                fp.write("Name\tType\tType Full\tSerial\tPN\tVendor\tModel\tMGMT IP\n")
                for host in myinv['result']:
                    if host['inventory']['type'] == "noinventory":
                        continue
                    fp.write(
                        "%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n" %(
                            host['name'],
                            host['inventory']['type'],
                            host['inventory']['type_full'],
                            host['inventory']['serialno_a'],
                            host['inventory']['serialno_b'],
                            host['inventory']['vendor'],
                            host['inventory']['model'],
                            host['inventory']['oob_ip']
                        )
                    )

    else:
        reply_text.append("Инвентарная информация не найдена")
    return reply_text, reply_file

def main():
    global tg
    #global zbx
    global me
    TelegramAPI = zbxtg.TelegramAPI
    ZabbixWeb = zbxtg.ZabbixWeb
    tmp_dir = zbxtg_settings.zbx_tg_tmp_dir

    if not zbxtg_daemon.zbx_tg_daemon_enabled:
        print("You should enable daemon by adding 'zbx_tg_daemon_enabled' in the configuration file")
        sys.exit(1)

    #tmp_uids = tmp_dir + "/uids.txt"
    tmp_ts = {
        "message_id": tmp_dir + "/daemon_message_id",
        "update_offset": tmp_dir + "/update_offset.txt",
    }

    for i, v in tmp_ts.items():
        if not os.path.exists(v):
            print_message("{0} doesn't exist, creating new one...".format(v))
            file_write(v, "0")
            print_message("{0} successfully created".format(v))

    update_id = file_read(tmp_ts["update_offset"])

    tg = TelegramAPI(key=zbxtg_settings.tg_key)
    tg.markdown = False
    tg.html = True

    if zbxtg_settings.proxy_to_tg:
        proxy_to_tg = zbxtg_settings.proxy_to_tg
        if not proxy_to_tg.find("http") and not proxy_to_tg.find("socks"):
            proxy_to_tg = "https://" + proxy_to_tg
        tg.proxies = {
            "https": "socks5://{0}".format(zbxtg_settings.proxy_to_tg),
            "http": "socks5://{0}".format(zbxtg_settings.proxy_to_tg),
            #"socks5": "socks5://{0}".format(zbxtg_settings.proxy_to_tg),
        }

    me = tg.get_me()
    print(me)

    def md5(fname):
        hash_md5 = hashlib.md5()
        with open(fname, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()

    md5sum = md5("/usr/lib/zabbix/alertscripts/zbxtgBot.py")
    print(md5sum)

    try:
        while True:
            time.sleep(2)
            md5sum_new = md5("/usr/lib/zabbix/alertscripts/zbxtgBot.py")
            if md5sum != md5sum_new:
                print("Bot was changed! Exiting...")
                sys.exit(1)
            tg.update_offset = update_id
            tg.reply_to_message_id = None
            # print("Update offset - {0}".format(tg.update_offset))
            updates = tg.get_updates()
            # print(updates)
            if not updates["result"]:
                continue
            for m in updates["result"]:
                #print(m)
                if "message" not in m and "channel_post" not in m:
                    continue
                if "message" in m:
                    if m["message"]["chat"]["id"] in zbxtg_daemon.zbx_tg_daemon_ignore_ids:
                        continue
                if "channel_post" in m:
                    if m["channel_post"]["chat"]["id"] in zbxtg_daemon.zbx_tg_daemon_ignore_ids:
                        continue
                update_id_last = m["update_id"]
                tg.update_offset = update_id_last
                if "message" in m:
                    m1 = m["message"]
                    to = m["message"]["chat"]["id"]
                elif "channel_post" in m:
                    m1 = m["channel_post"]
                    to = m["channel_post"]["chat"]["id"]
                message_id_file = tmp_dir + "/daemon_message_id_" + str(to) + ".txt"
                if not os.path.exists(message_id_file):
                    print_message("{0} doesn't exist, creating new one...".format(message_id_file))
                    file_write(message_id_file, "0")
                    print_message("{0} successfully created".format(message_id_file))
                if m1["chat"]["id"] not in zbxtg_daemon.zbx_tg_daemon_enabled_ids:
                    #file_write(tmp_ts["update_offset"], update_id_last)
                    message_id_last = file_read(message_id_file)[0].strip()
                    # print("Message id {0} {1}".format(m["message"]["message_id"], message_id_last))
                    if message_id_last:
                        message_id_last = int(message_id_last)
                    if m1["message_id"] > message_id_last:
                        print("Fuck this shit, I'm not going to answer to someone not from the whitelist")
                        reply_text = ["Извини, мы еще не знакомы. Обратись к системному администратору ({0}) и сообщи это число - {1}" \
                        .format(zbxtg_daemon.zbx_tg_daemon_enabled_admin, to)]
                        if tg.send_message(to, reply_text):
                            with open(message_id_file, "w") as message_id_file:
                                message_id_file.write(str(m1["message_id"]))
                            message_id_last = m1["message_id"]
                            tg.disable_web_page_preview = False
                else:
                    #print("{2} {3} - {0}: {1}".format(to, text, tg.update_offset, message_id_last))
                    message_id_last = file_read(message_id_file)[0].strip()
                    # print("Message id {0} {1}".format(m["message"]["message_id"], message_id_last))
                    if message_id_last:
                        message_id_last = int(message_id_last)
                    if m1["message_id"] > message_id_last:
                        chatid = str(m1["chat"]["id"])
                        if not "text" in m1:
                            continue

                        text = m1["text"]
                        reply_text = list()
                        reply_file = None
                        if m1["chat"]["type"] != "private":
                            tg.reply_to_message_id = m1["message_id"]
                        if re.search(r"^/chatid", text):
                            print("Chat: {0}, Command: {1}".format(to,text))
                            reply_text = ["{1} ID: {0}".format(to, m1["chat"]["type"])]
                        if re.search(r"^/(start|help)", text):
                            print("Chat: {0}, Command: {1}".format(to,text))
                            cmd_help(reply_text)

                        if re.search(r"^/problems", text) or re.search(r"^/alerts", text)\
                            or re.search(r"^/inventory", text):
                            zbx_api_user = None
                            zbx_api_pass = None
                            try:
                                print("chatid:", chatid)
                                #print(zbxtg_daemon.tg_zbx_mappings)
                                #print(zbxtg_daemon.tg_zbx_mappings["387365373"])
                                zbx_api_user = zbxtg_daemon.tg_zbx_mappings[chatid]
                                zbx_api_pass = zbxtg_daemon.zbx_users[zbx_api_user]
                                print("zbx_user:", zbx_api_user)
                                print("zbx_pass", zbx_api_pass)
                                zbx = ZabbixWeb(server=zbxtg_settings.zbx_server, username=zbx_api_user,
                                                password=zbx_api_pass)
                                zbx_api_verify = zbxtg_settings.zbx_api_verify
                                zbx.verify = zbx_api_verify
                            except:
                                pass
                            try:
                                if zbx_api_user and zbx_api_pass:
                                    zbx.login()
                                    zbx.api_test()

                                    print("Chat: {0}, Command: {1}".format(to,text))

                                    if re.search(r"^/problems", text):
                                        reply_text = cmd_problems(reply_text, zbx)
                                        if not reply_text:
                                            reply_text = ["Проблемы не найдены"]
                                        zbx = None
                                    if re.search(r"^/alerts", text):
                                        reply_text = cmd_alerts(reply_text, zbx)
                                        if not reply_text:
                                            reply_text = ["Алерты не найдены"]
                                        zbx = None
                                    if re.search(r"^/inventory", text):
                                        reply_text, reply_file = cmd_inventory(reply_text, zbx)
                                        zbx = None
                                else:
                                    reply_text = ["Нет учетной записи в системе мониторинга"]
                            except:
                                pass

                        if not reply_text and not reply_file:
                            continue
                            # reply_text = ["Извини, я не знаю, что ответить! Для подсказок набери /help"]
                        # replace text with emojis
                        if hasattr(zbxtg_settings, "emoji_map"):
                            reply_text_emoji_support = []
                            for l in reply_text:
                                l_new = l
                                for k, v in list(zbxtg_settings.emoji_map.items()):
                                    l_new = l_new.replace("{{" + k + "}}", v)
                                reply_text_emoji_support.append(l_new)
                            reply_text = reply_text_emoji_support

                        if reply_file:
                            tg.send_file(to, reply_text, reply_file)
                            os.remove(reply_file)
                            with open(message_id_file, "w") as message_id_file:
                                message_id_file.write(str(m1["message_id"]))
                            message_id_last = m1["message_id"]
                            tg.disable_web_page_preview = False
                        elif tg.send_message(to, reply_text):
                            with open(message_id_file, "w") as message_id_file:
                                message_id_file.write(str(m1["message_id"]))
                            message_id_last = m1["message_id"]
                            tg.disable_web_page_preview = False
                file_write(tmp_ts["update_offset"], update_id_last)
                update_id = update_id_last
    except KeyboardInterrupt:
        print("Exiting...")


if __name__ == "__main__":
    main()
