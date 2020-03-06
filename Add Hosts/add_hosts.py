#!/usr/bin/env python
# coding: utf-8
# encoding=utf8
version = "1.0.0"

import os
import ssl
import sys
reload(sys)
sys.setdefaultencoding('utf8')
import re
import json
import argparse
import logging
import logging.handlers
import timeit
import time
import multiprocessing as mp
import threading as mt
from operator import itemgetter

from tom_common import initialize
from tom_common import setup_logging
from tom_common import zabbix_request

#===============================================================================
def add_host(env, host, auth):
    logger = logging.getLogger('tom')
    logger.info("Adding HOST <{0}> to ZABBIX".format(host['name']))

    method = "host.create"
    params = {
        "host": host['name'],
        "interfaces": [],
        "groups": [
            {
                "groupid": '5' # Discovered hosts
            }
        ]
    }
    if "agent" in host:
        tmp = {
            "type": 1,
            "main": 1,
            "useip": 1,
            "ip": host['agent'],
            "dns": "",
            "port": "10050"
        }
        params['interfaces'].append(tmp)

    if "snmp" in host:
        tmp = {
            "type": 2,
            "main": 1,
            "useip": 1,
            "ip": host['snmp'],
            "dns": "",
            "port": "161",
            "bulk": 0
        }
        params['interfaces'].append(tmp)

    result = zabbix_request(env["zabbix_api_url"], method, params, auth)

    return result
#===============================================================================
def main():
    # Parsing parameters
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--version', '-v', action="store_true",
        help="Version info")
    parser.add_argument(
        '--debug', '-d', action="store_true",
        help="Run in debug mode")
    parser.add_argument(
        '--agentid', '-a', action="store",
        help="Agent ID")

    group = parser.add_mutually_exclusive_group(required=False)
    group.add_argument('--devices', '-s', action="store_true",
                       help="Update devices")
    group.add_argument('--links', '-l', action="store_true",
                       help="Update links")

    args = parser.parse_args()
    args.nodeid = args.agentid

    if args.version:
        print("%s" % (version))
        sys.exit()
    # Initialyzing environment
    module = {
        "subname" : "_common_hosts_add"
        }
    env = initialize(args, module)

    if env:
        logfile = "".join([env["module_logdir"], "/", args.agentid, ".log"])
        setup_logging(env, logfile)

        logger = logging.getLogger('tom')
        logger.info("Script started")

        scriptstart = timeit.default_timer()

        logger.info("Authenticating on server %s" % env["zabbix_api_url"])
        method = "user.login"
        params = {
            "user" : env["zabbix_api_user"],
            "password" : env["zabbix_api_password"]
            }
        auth = zabbix_request(env["zabbix_api_url"], method, params, None)
        logger.debug("Auth:\n%s" %
                     json.dumps(auth, indent=4, separators=(',', ': '))
                     )
        if "error" in auth:
            print("Error in authorization request. See logs for details")
            logger.error("Error in authorization request:\n%s" %
                         json.dumps(auth["error"],
                                    indent=4,
                                    separators=(',', ': ')
                                    )
                         )
            logger.info("Exiting!")
            sys.exit()

        with open('hosts.txt', 'r') as f:
          for line in f:
            # print(line)
            temp_arr = line.replace("\n", "").split(";")
            if temp_arr:
                if temp_arr[0] == "name":
                    continue
                # print(temp_arr)
                host = {
                    "name": temp_arr[0]
                }
                if len(temp_arr) > 1:
                    host['agent'] = temp_arr[1]
                if len(temp_arr) > 2:
                    host['snmp'] = temp_arr[2]
                print(host)
                result = add_host(env, host, auth)
                logger.info("Result:\n%s" %
                                json.dumps(result,
                                        indent=4,
                                        separators=(',', ': ')
                                        )
                                )
                if "error" in result:
                    sys.exit()

        scriptend = timeit.default_timer()
        
        logger.info("Script completed in %s seconds" %\
                    (str(scriptend - scriptstart)))
    else:
        print("Initialization failed! Exiting")

if __name__ == "__main__":
    main()
